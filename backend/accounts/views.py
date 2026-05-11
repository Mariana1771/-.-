from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest
from django.http import HttpResponse
from django.http import JsonResponse
from django.urls import reverse
from django.shortcuts import resolve_url
from django.core.mail import send_mail
from django.core.mail.backends.smtp import EmailBackend
from django.core.mail import EmailMessage
from learning.models import UserProfile, LessonProgress, QuizAttempt, Lesson, PremiumPayment
from .models import PaymentProviderConfig
from .models import (
    ReferralProfile,
    CertificateExamRequest,
    CertificatePayment,
    CertificateProgram,
    CertificateEnrollment,
    CertificateIssue,
    CertificateProgramLesson,
)
import uuid
import json
import base64
import hashlib
import random
import re
import math
import os
from urllib.parse import urlencode
from urllib.request import urlopen, Request

import stripe


def _is_modal_auth_request(request) -> bool:
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def _next_redirect_target(request) -> str:
    raw = (request.POST.get('next') or request.GET.get('next') or '').strip()
    if not raw:
        return reverse('dashboard')
    if raw.startswith('/') and not raw.startswith('//'):
        return raw
    try:
        return resolve_url(raw)
    except Exception:
        return reverse('dashboard')


def _get_or_create_program(program_slug: str) -> CertificateProgram:
    slug = (program_slug or '').strip().lower()
    defaults_map = {
        'a1': ('A1 Slovak Program', 'A1'),
        'a2': ('A2 Slovak Program', 'A2'),
        'b1': ('B1 Slovak Program', 'B1'),
        'b2': ('B2 Slovak Program', 'B2'),
    }
    title, level = defaults_map.get(slug, ('A1 Slovak Program', 'A1'))
    obj, _ = CertificateProgram.objects.get_or_create(
        slug=slug,
        defaults={
            'title': title,
            'level': level,
            'short_pitch': f'Пройди програму {level}, склади фінальний тест і отримай сертифікат.',
            'description_html': '',
            'required_lessons_percent': 80,
            'required_quiz_percent': 70,
        },
    )
    return obj


def _get_enrollment(user: User, program: CertificateProgram) -> CertificateEnrollment | None:
    if not user or not getattr(user, 'is_authenticated', False):
        return None
    obj = CertificateEnrollment.objects.filter(user=user, program=program).select_related('program', 'payment').first()
    if obj:
        return obj
    # Enrollment is free (A1 content is free); payment unlocks final exam + certificate issuance.
    return CertificateEnrollment.objects.create(user=user, program=program, status=CertificateEnrollment.STATUS_ACTIVE)


def _cert_is_paid(enrollment: CertificateEnrollment | None) -> bool:
    if not enrollment:
        return False
    p = getattr(enrollment, 'payment', None)
    return bool(p and p.status == CertificatePayment.STATUS_SUCCESS)


def _certificate_exam_state(user: User, program: CertificateProgram) -> dict:
    """
    Compute certificate exam progress based on existing learning tracking:
    - Completed A1 lessons: LessonProgress.completed + lesson.level='A1'
    - Final A1 Quiz: latest QuizAttempt(level='A1', is_final=True)
    """
    program_lessons_qs = CertificateProgramLesson.objects.filter(program=program).select_related('lesson')
    program_lesson_ids = list(program_lessons_qs.values_list('lesson_id', flat=True))
    total_a1_lessons = len(program_lesson_ids)
    required_lessons = max(1, math.ceil(total_a1_lessons * (program.required_lessons_percent / 100.0))) if total_a1_lessons else 0

    completed_lessons = LessonProgress.objects.filter(
        user=user,
        completed=True,
        lesson_id__in=program_lesson_ids,
    ).count()

    latest_quiz = QuizAttempt.objects.filter(user=user, level=program.level, is_final=True).order_by('-taken_at').first()
    latest_quiz_percent = latest_quiz.percent if latest_quiz else 0

    lessons_ok = completed_lessons >= required_lessons
    rq = int(program.required_quiz_percent or 0)
    quiz_ok = True if rq <= 0 else bool(latest_quiz and latest_quiz_percent >= rq)
    all_ok = lessons_ok and quiz_ok

    return {
        'required_lessons': required_lessons,
        'required_lessons_percent': int(program.required_lessons_percent),
        'required_quiz_percent': int(program.required_quiz_percent),
        'total_a1_lessons': total_a1_lessons,
        'completed_lessons': completed_lessons,
        'program_lessons': program_lessons_qs.order_by('order', 'id'),
        'latest_quiz': latest_quiz,
        'latest_quiz_percent': latest_quiz_percent,
        'lessons_ok': lessons_ok,
        'quiz_ok': quiz_ok,
        'all_ok': all_ok,
    }

def register_view(request):
    if request.user.is_authenticated:
        if _is_modal_auth_request(request):
            return JsonResponse({'ok': True, 'redirect': reverse('dashboard')})
        return redirect('dashboard')

    next_url = (request.GET.get('next') or request.POST.get('next') or '').strip()
    errors = {}
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')

        # Валідація
        if not name:
            errors['name'] = "Введи своє ім'я"
        if not username:
            errors['username'] = 'Введи логін'
        elif User.objects.filter(username=username).exists():
            errors['username'] = 'Цей логін вже зайнятий'
        
        if len(password) < 6:
            errors['password'] = 'Пароль має бути не менше 6 символів'
        elif password != password2:
            errors['password2'] = 'Паролі не співпадають'

        if not errors:
            # Створення користувача та профілю
            user = User.objects.create_user(
                username=username, 
                password=password, 
                first_name=name
            )
            UserProfile.objects.get_or_create(user=user)

            # create referral profile (for user's own code)
            ReferralProfile.get_or_create_for_user(user)
            
            login(request, user)
            messages.success(request, f'Ласкаво просимо, {name}!')
            target = _next_redirect_target(request)
            if _is_modal_auth_request(request):
                return JsonResponse({'ok': True, 'redirect': target})
            return redirect(target)

        if _is_modal_auth_request(request):
            return JsonResponse({'ok': False, 'errors': errors}, status=400)

    # Передаємо request.POST як 'form', щоб зберегти введені дані в полях при помилці
    return render(request, 'accounts/register.html', {
        'errors': errors,
        'form': request.POST if request.method == 'POST' else None,
        'next': next_url,
    })

def login_view(request):
    if request.user.is_authenticated:
        if _is_modal_auth_request(request):
            return JsonResponse({'ok': True, 'redirect': _next_redirect_target(request)})
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            target = _next_redirect_target(request)
            if _is_modal_auth_request(request):
                return JsonResponse({'ok': True, 'redirect': target})
            return redirect(target)

        if _is_modal_auth_request(request):
            return JsonResponse({'ok': False, 'error': 'Невірний логін або пароль'}, status=400)
        return render(request, 'accounts/login.html', {
            'error': 'Невірний логін або пароль',
            'username': username
        })

    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def profile_view(request):
    # Гарантуємо наявність профілю
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    # Обробка завантаження аватара
    if request.method == 'POST' and request.FILES.get('avatar'):
        profile.avatar = request.FILES['avatar']
        profile.save()
        messages.success(request, 'Фото профілю оновлено!')
        return redirect('profile')

    # Статистика для профілю
    completed = LessonProgress.objects.filter(user=request.user, completed=True).count()
    total_lessons = Lesson.objects.count()
    quiz_count = QuizAttempt.objects.filter(user=request.user).count()
    
    ref = ReferralProfile.get_or_create_for_user(request.user)
    return render(request, 'accounts/profile.html', {
        'profile': profile,
        'completed': completed,
        'total_lessons': total_lessons,
        'quiz_count': quiz_count,
        'ref_code': ref.code,
    })


@login_required
def premium_page(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    price_month_uah = 199
    cfg = PaymentProviderConfig.get_solo()
    ref = ReferralProfile.get_or_create_for_user(request.user)
    has_ref_discount = bool(ref.referred_by_id and not ref.discount_used)
    email_configured = bool((getattr(settings, 'EMAIL_HOST_USER', '') and getattr(settings, 'EMAIL_HOST_PASSWORD', '')) or (cfg.gmail_user and cfg.gmail_app_password))
    sms_configured = bool(getattr(settings, 'TURBOSMS_TOKEN', '') or cfg.turbosms_token)
    simple_otp = request.session.get('simple_premium_otp') or {}
    simple_otp_contact = (simple_otp.get('contact') or '').strip()
    return render(request, 'accounts/premium.html', {
        'profile': profile,
        'ref_code': ref.code,
        'price_uah': int(price_month_uah * (0.8 if has_ref_discount else 1)),
        'price_3m_uah': int(price_month_uah * 3 * (0.8 if has_ref_discount else 1)),
        'price_year_uah': int(price_month_uah * 12 * (0.8 if has_ref_discount else 1)),
        'debug': settings.DEBUG,
        'simple_otp_contact': simple_otp_contact,
        'email_configured': email_configured,
        'sms_configured': sms_configured,
        'has_ref_discount': has_ref_discount,
    })


@login_required
def premium_send_code(request):
    if not settings.DEBUG:
        messages.error(request, 'Ця дія доступна лише в тестовому режимі.')
        return redirect('premium_page')
    if request.method != 'POST':
        return redirect('premium_page')

    # collect form data
    try:
        period = int((request.POST.get('period_months') or '1').strip())
    except ValueError:
        period = 1
    if period not in (1, 3, 12):
        period = 1

    full_name = (request.POST.get('full_name') or '').strip()
    contact = (request.POST.get('contact') or '').strip()
    reference = (request.POST.get('reference') or '').strip()
    agree = request.POST.get('agree')

    if not full_name or not contact or not reference or not agree:
        messages.error(request, 'Заповніть усі поля, щоб отримати код підтвердження.')
        return redirect('premium_page')

    # simple throttle
    now_ts = int(timezone.now().timestamp())
    otp = request.session.get('premium_otp') or {}
    last_sent = int(otp.get('sent_at') or 0)
    if last_sent and (now_ts - last_sent) < 30:
        messages.warning(request, 'Код уже надіслано. Спробуйте ще раз через 30 секунд.')
        return redirect('premium_page')

    code = f"{random.randint(0, 999999):06d}"
    otp_hash = hashlib.sha256(code.encode('utf-8')).hexdigest()

    otp = {
        'sent_at': now_ts,
        'hash': otp_hash,
        'contact': contact,
        'period': period,
        'full_name': full_name[:80],
        'reference': reference[:120],
    }
    request.session['premium_otp'] = otp

    cfg = PaymentProviderConfig.get_solo()

    def _normalize_phone(value: str) -> str:
        raw = re.sub(r'[\s\-\(\)]', '', value or '')
        raw = raw.replace('+', '')
        # If user entered 0XXXXXXXXX, convert to 380XXXXXXXXX
        if raw.startswith('0') and len(raw) == 10:
            raw = '38' + raw
        return raw

    def _send_sms_turbosms(phone: str, text: str) -> bool:
        token = (getattr(settings, 'TURBOSMS_TOKEN', '') or cfg.turbosms_token or '').strip()
        sender = (getattr(settings, 'TURBOSMS_SENDER', '') or cfg.turbosms_sender or 'TurboSMS').strip()
        if not token:
            return False
        payload = {
            'recipients[0]': phone,
            'sms[sender]': sender,
            'sms[text]': text,
            'token': token,
        }
        data = urlencode(payload).encode('utf-8')
        req = Request('https://api.turbosms.ua/message/send.json', data=data, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        with urlopen(req, timeout=10) as r:
            body = r.read().decode('utf-8')
        try:
            resp = json.loads(body)
        except Exception:
            return False
        # TurboSMS docs: response_status==0 => OK
        if resp.get('response_status') == 0:
            return True
        status = resp.get('response_status') or resp.get('status') or resp.get('response_code')
        return str(status) in ('0', '200', 'OK')

    is_email = bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', contact))
    if is_email:
        gmail_user = (getattr(settings, 'EMAIL_HOST_USER', '') or cfg.gmail_user or '').strip()
        gmail_pass = (getattr(settings, 'EMAIL_HOST_PASSWORD', '') or cfg.gmail_app_password or '').strip().replace(' ', '')
        if not (gmail_user and gmail_pass):
            messages.error(request, 'Email не налаштовано. Заповніть Gmail дані в адмінці (Конфіг оплат/OTP).')
            return redirect('premium_page')
        try:
            backend = EmailBackend(
                host='smtp.gmail.com',
                port=587,
                username=gmail_user,
                password=gmail_pass,
                use_tls=True,
                fail_silently=False,
            )
            msg = EmailMessage(
                subject='Код підтвердження Premium',
                body=f'Ваш код підтвердження: {code}\n\nЯкщо ви не запитували цей код — ігноруйте повідомлення.',
                from_email=gmail_user,
                to=[contact],
                connection=backend,
            )
            msg.send(fail_silently=False)
            messages.success(request, 'Код надіслано на email. Перевірте пошту.')
        except Exception:
            messages.error(request, 'Не вдалося надіслати email. Перевірте SMTP налаштування Gmail (app password) та спробуйте ще раз.')
    else:
        phone = _normalize_phone(contact)
        if not re.fullmatch(r'\d{11,15}', phone):
            messages.error(request, 'Невірний номер телефону. Введіть у форматі +380XXXXXXXXX або 0XXXXXXXXX.')
            return redirect('premium_page')

        sms_text = f'Код підтвердження Premium: {code}'
        if not (getattr(settings, 'TURBOSMS_TOKEN', '') or cfg.turbosms_token):
            messages.error(request, 'SMS не налаштовано. Заповніть TurboSMS token в адмінці (Конфіг оплат/OTP).')
            return redirect('premium_page')
        ok = False
        try:
            ok = _send_sms_turbosms(phone, sms_text)
        except Exception:
            ok = False

        if ok:
            messages.success(request, 'Код надіслано на номер телефону.')
        else:
            messages.error(request, 'SMS не надіслано. Перевірте налаштування TurboSMS (TURBOSMS_TOKEN, TURBOSMS_SENDER).')

    return redirect('premium_page')


def _is_email(value: str) -> bool:
    return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', (value or '').strip()))


def _normalize_phone(value: str) -> str:
    raw = re.sub(r'[\s\-\(\)]', '', value or '')
    raw = raw.replace('+', '')
    if raw.startswith('0') and len(raw) == 10:
        raw = '38' + raw
    return raw


def _send_otp_to_contact(contact: str, code: str, subject: str, sms_prefix: str) -> tuple[bool, str]:
    """
    Returns (ok, error_message)
    """
    cfg = PaymentProviderConfig.get_solo()

    if _is_email(contact):
        gmail_user = (getattr(settings, 'EMAIL_HOST_USER', '') or cfg.gmail_user or '').strip()
        gmail_pass = (getattr(settings, 'EMAIL_HOST_PASSWORD', '') or cfg.gmail_app_password or '').strip().replace(' ', '')
        if not (gmail_user and gmail_pass):
            return False, 'Email не налаштовано. Заповніть Gmail дані в адмінці (Конфіг оплат/OTP).'
        try:
            backend = EmailBackend(
                host='smtp.gmail.com',
                port=587,
                username=gmail_user,
                password=gmail_pass,
                use_tls=True,
                fail_silently=False,
            )
            msg = EmailMessage(
                subject=subject,
                body=f'Ваш код підтвердження: {code}\n\nЯкщо ви не запитували цей код — ігноруйте повідомлення.',
                from_email=gmail_user,
                to=[contact],
                connection=backend,
            )
            msg.send(fail_silently=False)
            return True, ''
        except Exception as e:
            base = 'Не вдалося надіслати email. Перевірте Gmail (2FA + App Password) та спробуйте ще раз.'
            if settings.DEBUG:
                return False, f'{base} Тех.деталі: {type(e).__name__}: {e}'
            return False, base

    phone = _normalize_phone(contact)
    if not re.fullmatch(r'\d{11,15}', phone):
        return False, 'Невірний номер телефону. Введіть у форматі +380XXXXXXXXX або 0XXXXXXXXX.'

    token = (getattr(settings, 'TURBOSMS_TOKEN', '') or cfg.turbosms_token or '').strip()
    sender = (getattr(settings, 'TURBOSMS_SENDER', '') or cfg.turbosms_sender or 'TurboSMS').strip()
    if not token:
        return False, 'SMS не налаштовано. Заповніть TurboSMS token в адмінці (Конфіг оплат/OTP).'

    payload = {
        'recipients[0]': phone,
        'sms[sender]': sender,
        'sms[text]': f'{sms_prefix}: {code}',
        'token': token,
    }
    data = urlencode(payload).encode('utf-8')
    req = Request('https://api.turbosms.ua/message/send.json', data=data, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    try:
        with urlopen(req, timeout=10) as r:
            body = r.read().decode('utf-8')
        resp = json.loads(body)
    except Exception as e:
        base = 'SMS не надіслано. Перевірте налаштування TurboSMS та спробуйте ще раз.'
        if settings.DEBUG:
            return False, f'{base} Тех.деталі: {type(e).__name__}: {e}'
        return False, base

    if resp.get('response_status') == 0:
        return True, ''
    status = resp.get('response_status') or resp.get('status') or resp.get('response_code')
    if str(status) in ('0', '200', 'OK'):
        return True, ''
    return False, 'SMS не надіслано. Перевірте налаштування TurboSMS (TURBOSMS_TOKEN, TURBOSMS_SENDER).'


def _send_receipt_email(to_email: str, subject: str, body: str) -> tuple[bool, str]:
    cfg = PaymentProviderConfig.get_solo()
    gmail_user = (getattr(settings, 'EMAIL_HOST_USER', '') or cfg.gmail_user or '').strip()
    gmail_pass = (getattr(settings, 'EMAIL_HOST_PASSWORD', '') or cfg.gmail_app_password or '').strip().replace(' ', '')
    if not (gmail_user and gmail_pass):
        return False, 'Email не налаштовано.'
    try:
        backend = EmailBackend(
            host='smtp.gmail.com',
            port=587,
            username=gmail_user,
            password=gmail_pass,
            use_tls=True,
            fail_silently=False,
        )
        msg = EmailMessage(
            subject=subject,
            body=body,
            from_email=gmail_user,
            to=[to_email],
            connection=backend,
        )
        msg.send(fail_silently=False)
        return True, ''
    except Exception as e:
        if settings.DEBUG:
            return False, f'{type(e).__name__}: {e}'
        return False, 'send_failed'


def _extract_card_last4(card_number: str) -> str:
    digits = re.sub(r'\D', '', card_number or '')
    if len(digits) < 12 or len(digits) > 19:
        return ''
    return digits[-4:]


def _extract_contact_email_from_reference(reference: str) -> str:
    """
    Extract CONTACT=email from payment reference like:
    'SIMPLE | CARD_LAST4=1234 | CONTACT=name@example.com'
    """
    ref = reference or ''
    m = re.search(r'CONTACT=([^|\s]+)', ref)
    if not m:
        return ''
    return (m.group(1) or '').strip()[:120]


def _build_certificate_pdf_bytes(
    cert_id: str,
    date_str: str,
    program_title: str,
    program_level: str,
    full_name: str,
    result_line: str,
) -> bytes:
    from io import BytesIO
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A5
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    buf = BytesIO()
    # Use A5 portrait to avoid "too long" empty page.
    c = canvas.Canvas(buf, pagesize=A5)
    w, h = A5

    # Register fonts with Cyrillic support (Windows has Arial).
    # Fallbacks keep PDF generation working even if font is missing.
    font_regular = "Helvetica"
    font_bold = "Helvetica-Bold"
    try:
        arial = r"C:\Windows\Fonts\arial.ttf"
        arial_bold = r"C:\Windows\Fonts\arialbd.ttf"
        if os.path.exists(arial) and os.path.exists(arial_bold):
            if "CertArial" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("CertArial", arial))
            if "CertArialBold" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("CertArialBold", arial_bold))
            font_regular = "CertArial"
            font_bold = "CertArialBold"
    except Exception:
        pass

    # background
    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, w, h, fill=1, stroke=0)

    # Compact layout for A5
    margin = 28

    # subtle corner blobs (keep premium, not noisy)
    try:
        c.setFillColor(colors.Color(0.86, 0.12, 0.47, alpha=0.06))  # pink
        c.circle(margin + 22, h - margin - 22, 58, stroke=0, fill=1)
        c.setFillColor(colors.Color(0.05, 0.65, 0.92, alpha=0.06))  # blue
        c.circle(w - margin - 18, h - margin - 18, 64, stroke=0, fill=1)
    except Exception:
        pass

    c.setStrokeColor(colors.HexColor("#e5e7eb"))
    c.setLineWidth(2)
    c.roundRect(margin, margin, w - 2 * margin, h - 2 * margin, 18, stroke=1, fill=0)

    # header
    c.setFillColor(colors.HexColor("#0f172a"))
    c.setFont(font_bold, 11)
    c.drawString(margin + 14, h - margin - 22, "SLOVAK.SK")

    c.setFillColor(colors.HexColor("#64748b"))
    c.setFont(font_bold, 9)
    c.drawRightString(w - margin - 14, h - margin - 22, f"ID: {cert_id}   Date: {date_str}")

    # title
    c.setFillColor(colors.HexColor("#0f172a"))
    c.setFont(font_bold, 20)
    c.drawCentredString(w / 2, h - margin - 78, "Certificate of Completion")

    c.setFillColor(colors.HexColor("#475569"))
    c.setFont(font_bold, 10)
    c.drawCentredString(w / 2, h - margin - 98, f"{program_title} ({program_level})")

    # body
    c.setFillColor(colors.HexColor("#64748b"))
    c.setFont(font_bold, 10)
    c.drawCentredString(w / 2, h - margin - 132, "This certifies that")

    c.setFillColor(colors.HexColor("#db2777"))
    c.setFont(font_bold, 20)
    c.drawCentredString(w / 2, h - margin - 164, full_name)

    c.setFillColor(colors.HexColor("#475569"))
    c.setFont(font_regular, 10)
    c.drawCentredString(w / 2, h - margin - 192, "has successfully completed the certification program on the platform.")

    # result box
    c.setFillColor(colors.HexColor("#f8fafc"))
    c.setStrokeColor(colors.HexColor("#e2e8f0"))
    c.setLineWidth(1)
    box_w = w - 2 * margin - 44
    box_x = (w - box_w) / 2
    # Move result box slightly down to reduce empty middle space
    box_y = h - margin - 218
    c.roundRect(box_x, box_y, box_w, 40, 14, stroke=1, fill=1)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.setFont(font_bold, 10)
    # Use a short ASCII line to avoid layout issues; full details are on the site.
    safe_line = result_line.strip()
    c.drawCentredString(w / 2, box_y + 14, safe_line[:120])

    # Bottom row (like site): cat left, signature mid, verification box right
    # Cat photo (bottom-left) if exists (transparent cutout)
    try:
        from reportlab.lib.utils import ImageReader
        cat_path = os.path.join(str(getattr(settings, 'MEDIA_ROOT', '')), 'cert_cat_cutout.png')
        if cat_path and os.path.exists(cat_path):
            img = ImageReader(cat_path)
            img_w = 150
            img_h = 110
            x = margin + 12
            # Move bottom visuals up to reduce empty space
            y = margin + 140
            c.drawImage(img, x, y, width=img_w, height=img_h, mask='auto', preserveAspectRatio=True, anchor='c')
    except Exception:
        pass

    # Signature (center-left, above cat area)
    sig_x = margin + 190
    sig_y = margin + 224
    c.setStrokeColor(colors.HexColor("#db2777"))
    c.setLineWidth(2)
    c.line(sig_x, sig_y, sig_x + 150, sig_y)
    c.setFillColor(colors.HexColor("#64748b"))
    c.setFont(font_bold, 9)
    c.drawString(sig_x, sig_y - 14, "Platform signature")
    c.setFillColor(colors.HexColor("#0f172a"))
    c.setFont(font_bold, 10)
    c.drawString(sig_x, sig_y - 30, "Slovak.sk")

    # Verification card (bottom-right)
    v_w = 170
    v_h = 78
    v_x = w - margin - 12 - v_w
    v_y = margin + 150
    c.setFillColor(colors.HexColor("#ffffff"))
    c.setStrokeColor(colors.HexColor("#e5e7eb"))
    c.setLineWidth(1)
    c.roundRect(v_x, v_y, v_w, v_h, 14, stroke=1, fill=1)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.setFont(font_bold, 10)
    c.drawString(v_x + 14, v_y + v_h - 22, "Verification")
    c.setFillColor(colors.HexColor("#94a3b8"))
    c.setFont(font_bold, 8)
    c.drawString(v_x + 14, v_y + v_h - 40, "ID")
    c.drawString(v_x + 14, v_y + v_h - 54, "DATE")
    c.setFillColor(colors.HexColor("#0f172a"))
    c.setFont(font_bold, 9)
    c.drawRightString(v_x + v_w - 14, v_y + v_h - 40, cert_id)
    c.drawRightString(v_x + v_w - 14, v_y + v_h - 54, date_str)
    c.setFillColor(colors.HexColor("#94a3b8"))
    c.setFont(font_regular, 8)
    c.drawString(v_x + 14, v_y + 14, "Use this ID to confirm authenticity.")

    c.showPage()
    c.save()
    return buf.getvalue()


def _stripe_is_configured() -> bool:
    return bool(getattr(settings, 'STRIPE_SECRET_KEY', '') and getattr(settings, 'STRIPE_PUBLIC_KEY', ''))


def _stripe_init():
    stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')


def _stripe_object_get(obj, key: str):
    """StripeObject не має dict `.get()`, тому читаємо через [] / dict / getattr."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(key)
    try:
        return obj[key]
    except Exception:
        return getattr(obj, key, None)


def _mark_premium_paid(payment: PremiumPayment) -> None:
    if not payment:
        return
    if payment.status != PremiumPayment.STATUS_SUCCESS:
        payment.status = PremiumPayment.STATUS_SUCCESS
        payment.paid_at = timezone.now()
        payment.save(update_fields=['status', 'paid_at'])
    profile, _ = UserProfile.objects.get_or_create(user=payment.user)
    if not profile.is_premium:
        profile.is_premium = True
        profile.save(update_fields=['is_premium'])


def _mark_certificate_paid(cp: CertificatePayment) -> None:
    if not cp:
        return
    if cp.status != CertificatePayment.STATUS_SUCCESS:
        cp.status = CertificatePayment.STATUS_SUCCESS
        cp.paid_at = timezone.now()
        cp.save(update_fields=['status', 'paid_at'])
    program = cp.program or _get_or_create_program('a1')
    enrollment, _ = CertificateEnrollment.objects.get_or_create(
        user=cp.user,
        program=program,
        defaults={'payment': cp, 'status': CertificateEnrollment.STATUS_ACTIVE},
    )
    if enrollment.payment_id != cp.id:
        enrollment.payment = cp
        enrollment.save(update_fields=['payment'])


@login_required
def premium_stripe_checkout(request):
    if request.method != 'POST':
        return redirect('premium_page')

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if profile.is_premium:
        messages.info(request, 'У вас вже активний Premium.')
        return redirect('premium_page')

    if not _stripe_is_configured():
        messages.error(request, 'Stripe не налаштовано. Додайте STRIPE_PUBLIC_KEY та STRIPE_SECRET_KEY в env.')
        return redirect('premium_page')

    try:
        period = int((request.POST.get('period_months') or '1').strip())
    except ValueError:
        period = 1
    if period not in (1, 3, 12):
        period = 1

    price_month_uah = 199
    ref = ReferralProfile.get_or_create_for_user(request.user)
    # Apply referral / discount code at payment time (optional)
    entered_code = (request.POST.get('discount_code') or request.POST.get('ref_code') or '').strip().upper()
    if entered_code and not ref.referred_by_id and not ref.discount_used:
        inviter = ReferralProfile.objects.filter(code=entered_code).select_related('user').first()
        if inviter and inviter.user_id != request.user.id:
            inviter_profile, _ = UserProfile.objects.get_or_create(user=inviter.user)
            if inviter_profile.is_premium:
                ref.referred_by = inviter.user
                ref.save(update_fields=['referred_by'])
            else:
                messages.warning(request, 'Код не дійсний для знижки: користувач не має Premium.')
        else:
            messages.warning(request, 'Код знижки недійсний.')
    has_discount = bool(ref.referred_by_id and not ref.discount_used)
    amount_uah = int(price_month_uah * period * (0.8 if has_discount else 1))

    order_id = uuid.uuid4().hex[:20].upper()
    payment = PremiumPayment.objects.create(
        user=request.user,
        amount_uah=amount_uah,
        period_months=period,
        status=PremiumPayment.STATUS_PENDING,
        transaction_id=order_id,
    )
    if has_discount:
        ref.discount_used = True
        ref.save(update_fields=['discount_used'])

    _stripe_init()
    success_url = request.build_absolute_uri(reverse('premium_stripe_success')) + '?session_id={CHECKOUT_SESSION_ID}'
    cancel_url = request.build_absolute_uri(reverse('premium_page'))

    session = stripe.checkout.Session.create(
        mode='payment',
        success_url=success_url,
        cancel_url=cancel_url,
        payment_method_types=['card'],
        line_items=[
            {
                'price_data': {
                    'currency': 'uah',
                    'unit_amount': int(amount_uah) * 100,
                    'product_data': {
                        'name': f'Premium доступ ({period} міс.)',
                    },
                },
                'quantity': 1,
            }
        ],
        metadata={
            'kind': 'premium',
            'tx': payment.transaction_id,
            'user_id': str(request.user.id),
            'period_months': str(period),
        },
        client_reference_id=str(request.user.id),
    )

    payment.reference = f"STRIPE | SESSION={session.id}"[:120]
    payment.save(update_fields=['reference'])

    return redirect(session.url, permanent=False)


@login_required
def premium_stripe_success(request):
    session_id = (request.GET.get('session_id') or '').strip()
    if not session_id:
        messages.error(request, 'Не вдалося підтвердити оплату (нема session_id).')
        return redirect('premium_page')

    if not _stripe_is_configured():
        messages.error(request, 'Stripe не налаштовано.')
        return redirect('premium_page')

    _stripe_init()
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except Exception as e:
        if settings.DEBUG:
            messages.error(request, f'Не вдалося отримати Stripe session: {type(e).__name__}: {e}')
        else:
            messages.error(request, 'Не вдалося підтвердити оплату.')
        return redirect('premium_page')

    payment_status = getattr(session, 'payment_status', None)
    if (payment_status or '') != 'paid':
        messages.warning(request, 'Оплата ще не підтверджена Stripe.')
        return redirect('premium_page')

    meta = getattr(session, 'metadata', None) or {}
    tx = (str(_stripe_object_get(meta, 'tx') or '')).strip()
    p = PremiumPayment.objects.filter(transaction_id=tx, user=request.user).first() if tx else None
    if not p:
        p = PremiumPayment.objects.filter(user=request.user, reference__contains=session_id).order_by('-created_at').first()
    if not p:
        messages.error(request, 'Платіж не знайдено.')
        return redirect('premium_page')

    _mark_premium_paid(p)
    messages.success(request, 'Оплата успішна! Premium активовано.')
    return redirect('premium_page')


@login_required
def certificate_stripe_checkout(request):
    if request.method != 'POST':
        return redirect('certificates_page')

    if not _stripe_is_configured():
        messages.error(request, 'Stripe не налаштовано. Додайте STRIPE_PUBLIC_KEY та STRIPE_SECRET_KEY в env.')
        return redirect('certificates_page')

    program_slug = (request.POST.get('program_slug') or '').strip().lower()
    program = _get_or_create_program(program_slug or 'a1')

    # reuse a recent pending payment to avoid duplicates
    payment = CertificatePayment.objects.filter(
        user=request.user,
        program=program,
        status=CertificatePayment.STATUS_PENDING,
        reference__startswith='STRIPE |',
    ).order_by('-created_at').first()

    if payment:
        payment.amount_eur = 25
        payment.save(update_fields=['amount_eur'])
    else:
        internal_id = uuid.uuid4().hex[:20].upper()
        payment = CertificatePayment.objects.create(
            user=request.user,
            program=program,
            amount_eur=25,
            status=CertificatePayment.STATUS_PENDING,
            transaction_id=internal_id,
        )

    _stripe_init()
    success_url = request.build_absolute_uri(reverse('certificate_stripe_success')) + '?session_id={CHECKOUT_SESSION_ID}'
    cancel_url = request.build_absolute_uri(reverse('certificates_page')) + f'?buy={program.slug}#pay'

    session = stripe.checkout.Session.create(
        mode='payment',
        success_url=success_url,
        cancel_url=cancel_url,
        payment_method_types=['card'],
        line_items=[
            {
                'price_data': {
                    'currency': 'eur',
                    'unit_amount': int(payment.amount_eur) * 100,
                    'product_data': {
                        'name': f'Сертифікація {program.level}: фінальний іспит + сертифікат',
                    },
                },
                'quantity': 1,
            }
        ],
        metadata={
            'kind': 'certificate',
            'tx': payment.transaction_id,
            'user_id': str(request.user.id),
            'program_slug': program.slug,
        },
        client_reference_id=str(request.user.id),
    )

    payment.reference = f"STRIPE | SESSION={session.id}"[:120]
    payment.save(update_fields=['reference'])

    return redirect(session.url, permanent=False)


@login_required
def certificate_stripe_success(request):
    session_id = (request.GET.get('session_id') or '').strip()
    if not session_id:
        messages.error(request, 'Не вдалося підтвердити оплату (нема session_id).')
        return redirect('certificates_page')

    if not _stripe_is_configured():
        messages.error(request, 'Stripe не налаштовано.')
        return redirect('certificates_page')

    _stripe_init()
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except Exception as e:
        if settings.DEBUG:
            messages.error(request, f'Не вдалося отримати Stripe session: {type(e).__name__}: {e}')
        else:
            messages.error(request, 'Не вдалося підтвердити оплату.')
        return redirect('certificates_page')

    payment_status = getattr(session, 'payment_status', None)
    if (payment_status or '') != 'paid':
        messages.warning(request, 'Оплата ще не підтверджена Stripe.')
        return redirect('certificates_page')

    meta = getattr(session, 'metadata', None) or {}
    tx = (str(_stripe_object_get(meta, 'tx') or '')).strip()
    cp = CertificatePayment.objects.filter(transaction_id=tx, user=request.user).select_related('program').first() if tx else None
    if not cp:
        cp = CertificatePayment.objects.filter(user=request.user, reference__contains=session_id).select_related('program').order_by('-created_at').first()
    if not cp:
        messages.error(request, 'Платіж не знайдено.')
        return redirect('certificates_page')

    _mark_certificate_paid(cp)
    messages.success(request, 'Оплата успішна! Іспит та сертифікат розблоковано.')
    return redirect('certificate_exam_path', program_slug=(cp.program.slug if cp.program else 'a1'))


@csrf_exempt
def stripe_webhook(request):
    # Webhook is recommended in production; success_url is still useful UX-wise.
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    wh_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '') or ''
    if not wh_secret:
        return HttpResponseBadRequest('Webhook secret not configured')

    _stripe_init()
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, wh_secret)
    except Exception:
        return HttpResponseBadRequest('Invalid signature')

    etype = event.get('type')
    obj = (event.get('data') or {}).get('object') or {}

    if etype in ('checkout.session.completed', 'checkout.session.async_payment_succeeded'):
        meta = obj.get('metadata') or {}
        kind = (meta.get('kind') or '').strip()
        tx = (meta.get('tx') or '').strip()
        if kind == 'premium' and tx:
            p = PremiumPayment.objects.filter(transaction_id=tx).select_related('user').first()
            if p:
                _mark_premium_paid(p)
        if kind == 'certificate' and tx:
            cp = CertificatePayment.objects.filter(transaction_id=tx).select_related('user', 'program').first()
            if cp:
                _mark_certificate_paid(cp)

    return HttpResponse('ok')

@login_required
def premium_simple_send_code(request):
    if request.method != 'POST':
        return redirect('premium_page')

    try:
        period = int((request.POST.get('period_months') or '1').strip())
    except ValueError:
        period = 1
    if period not in (1, 3, 12):
        period = 1

    card_number = (request.POST.get('card_number') or '').strip()
    contact = (request.POST.get('contact') or '').strip()
    agree = request.POST.get('agree')

    last4 = _extract_card_last4(card_number)
    if not last4:
        messages.error(request, 'Введіть коректний номер картки.')
        return redirect('premium_page')
    if not contact:
        messages.error(request, 'Введіть email, щоб отримати код підтвердження.')
        return redirect('premium_page')
    if not _is_email(contact):
        messages.error(request, 'Для підтвердження потрібен саме email.')
        return redirect('premium_page')
    if not agree:
        messages.error(request, 'Потрібно підтвердити згоду.')
        return redirect('premium_page')

    # throttle
    now_ts = int(timezone.now().timestamp())
    otp = request.session.get('simple_premium_otp') or {}
    last_sent = int(otp.get('sent_at') or 0)
    if last_sent and (now_ts - last_sent) < 30:
        messages.warning(request, 'Код уже надіслано. Спробуйте ще раз через 30 секунд.')
        return redirect('premium_page')

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if profile.is_premium:
        messages.info(request, 'У вас вже активний Premium.')
        return redirect('premium_page')

    price_month_uah = 199
    ref = ReferralProfile.get_or_create_for_user(request.user)
    has_discount = bool(ref.referred_by_id and not ref.discount_used)
    amount_uah = int(price_month_uah * period * (0.8 if has_discount else 1))

    # reuse a recent pending payment to avoid spamming rows
    payment = PremiumPayment.objects.filter(
        user=request.user,
        status=PremiumPayment.STATUS_PENDING,
        reference__startswith='SIMPLE |',
    ).order_by('-created_at').first()
    if payment:
        payment.amount_uah = amount_uah
        payment.period_months = period
        payment.reference = f'SIMPLE | CARD_LAST4={last4} | CONTACT={contact[:60]}'
        payment.save(update_fields=['amount_uah', 'period_months', 'reference'])
    else:
        internal_id = uuid.uuid4().hex[:20].upper()
        payment = PremiumPayment.objects.create(
            user=request.user,
            amount_uah=amount_uah,
            period_months=period,
            status=PremiumPayment.STATUS_PENDING,
            transaction_id=internal_id,
            reference=f'SIMPLE | CARD_LAST4={last4} | CONTACT={contact[:60]}',
        )
    if has_discount:
        ref.discount_used = True
        ref.save(update_fields=['discount_used'])

    code = f"{random.randint(0, 999999):06d}"
    otp_hash = hashlib.sha256(code.encode('utf-8')).hexdigest()
    sess_otp = {
        'sent_at': now_ts,
        'hash': otp_hash,
        'contact': contact,
        'payment_tx': payment.transaction_id,
    }
    if settings.DEBUG:
        sess_otp['plain'] = code
    request.session['simple_premium_otp'] = sess_otp

    ok, err = _send_otp_to_contact(contact, code, 'Підтвердження оплати Premium', 'Код підтвердження Premium')
    if not ok:
        if settings.DEBUG:
            messages.info(request, f'TEST код підтвердження: {code}')
        else:
            messages.error(request, err)
            return redirect('premium_page')

    messages.success(request, 'Код підтвердження надіслано. Введіть його нижче.')
    return redirect('premium_page')


@login_required
def premium_simple_confirm(request):
    if request.method != 'POST':
        return redirect('premium_page')

    code = (request.POST.get('otp_code') or '').strip()
    otp = request.session.get('simple_premium_otp') or {}
    if not otp.get('hash') or not otp.get('payment_tx'):
        messages.error(request, 'Спочатку надішліть код підтвердження.')
        return redirect('premium_page')
    if not re.fullmatch(r'\d{6}', code or ''):
        messages.error(request, 'Введіть 6-значний код.')
        return redirect('premium_page')

    if hashlib.sha256(code.encode('utf-8')).hexdigest() != otp.get('hash'):
        messages.error(request, 'Невірний код підтвердження.')
        if settings.DEBUG and otp.get('plain'):
            messages.info(request, f"TEST актуальний код: {otp.get('plain')}")
        return redirect('premium_page')

    tx = otp.get('payment_tx')
    p = PremiumPayment.objects.filter(transaction_id=tx, user=request.user).first()
    if not p:
        messages.error(request, 'Платіж не знайдено.')
        return redirect('premium_page')

    if p.status != PremiumPayment.STATUS_SUCCESS:
        p.status = PremiumPayment.STATUS_SUCCESS
        p.paid_at = timezone.now()
        p.save(update_fields=['status', 'paid_at'])
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.is_premium = True
        profile.save(update_fields=['is_premium'])

    # receipt email (with referral code/link)
    to_email = (otp.get('contact') or '').strip()
    if to_email and _is_email(to_email):
        paid_at = p.paid_at or timezone.now()
        ref = ReferralProfile.get_or_create_for_user(request.user)
        ref_code = ref.code
        ref_link = request.build_absolute_uri(f'/accounts/register/?ref={ref_code}')
        body = (
            "Квитанція / підтвердження оплати\n\n"
            "Тип: Premium доступ\n"
            f"Сума: {p.amount_uah} грн\n"
            f"Період: {p.period_months} міс.\n"
            f"Дата: {paid_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"Транзакція: {p.transaction_id}\n\n"
            "Запроси друга і він отримає знижку 20% на Premium:\n"
            f"Промокод: {ref_code}\n"
            f"Посилання: {ref_link}\n\n"
            "Дякуємо за оплату."
        )
        ok, err = _send_receipt_email(to_email, 'Квитанція: Premium оплачено', body)
        if not ok and settings.DEBUG:
            messages.info(request, f'Квитанцію не надіслано: {err}')

    if 'simple_premium_otp' in request.session:
        del request.session['simple_premium_otp']

    messages.success(request, 'Оплата підтверджена. Premium активовано.')
    return redirect('premium_page')


@login_required
def certificate_simple_send_code(request):
    program_slug = (request.POST.get('program_slug') or '').strip().lower()
    program = _get_or_create_program(program_slug or 'a1')
    if request.method != 'POST':
        return redirect('certificates_page')

    card_number = (request.POST.get('card_number') or '').strip()
    contact = (request.POST.get('contact') or '').strip()
    agree = request.POST.get('agree')

    last4 = _extract_card_last4(card_number)
    if not last4:
        messages.error(request, 'Введіть коректний номер картки.')
        return redirect('certificates_page')
    if not contact:
        messages.error(request, 'Введіть email, щоб отримати код підтвердження.')
        return redirect('certificates_page')
    if not _is_email(contact):
        messages.error(request, 'Для підтвердження потрібен саме email.')
        return redirect('certificates_page')
    if not agree:
        messages.error(request, 'Потрібно підтвердити згоду.')
        return redirect('certificates_page')

    now_ts = int(timezone.now().timestamp())
    otp = request.session.get('simple_cert_otp') or {}
    last_sent = int(otp.get('sent_at') or 0)
    if last_sent and (now_ts - last_sent) < 30:
        messages.warning(request, 'Код уже надіслано. Спробуйте ще раз через 30 секунд.')
        return redirect('certificates_page')

    payment = CertificatePayment.objects.filter(
        user=request.user,
        status=CertificatePayment.STATUS_PENDING,
        reference__startswith='SIMPLE |',
        program=program,
    ).order_by('-created_at').first()
    if payment:
        payment.amount_eur = 25
        payment.reference = f'SIMPLE | CARD_LAST4={last4} | CONTACT={contact[:60]}'
        payment.save(update_fields=['amount_eur', 'reference'])
    else:
        internal_id = uuid.uuid4().hex[:20].upper()
        payment = CertificatePayment.objects.create(
            user=request.user,
            program=program,
            amount_eur=25,
            reference=f'SIMPLE | CARD_LAST4={last4} | CONTACT={contact[:60]}',
            status=CertificatePayment.STATUS_PENDING,
            transaction_id=internal_id,
        )

    code = f"{random.randint(0, 999999):06d}"
    otp_hash = hashlib.sha256(code.encode('utf-8')).hexdigest()
    sess_otp = {
        'sent_at': now_ts,
        'hash': otp_hash,
        'contact': contact,
        'payment_tx': payment.transaction_id,
    }
    if settings.DEBUG:
        sess_otp['plain'] = code
    request.session['simple_cert_otp'] = sess_otp

    ok, err = _send_otp_to_contact(contact, code, 'Підтвердження оплати сертифікату', 'Код підтвердження')
    if not ok:
        if settings.DEBUG:
            messages.info(request, f'TEST код підтвердження: {code}')
        else:
            messages.error(request, err)
            return redirect('certificates_page')

    messages.success(request, 'Код підтвердження надіслано. Введіть його нижче.')
    return redirect('certificates_page')


@login_required
def certificate_simple_confirm(request):
    if request.method != 'POST':
        return redirect('certificates_page')

    code = (request.POST.get('otp_code') or '').strip()
    otp = request.session.get('simple_cert_otp') or {}
    if not otp.get('hash') or not otp.get('payment_tx'):
        messages.error(request, 'Спочатку надішліть код підтвердження.')
        return redirect('certificates_page')
    if not re.fullmatch(r'\d{6}', code or ''):
        messages.error(request, 'Введіть 6-значний код.')
        return redirect('certificates_page')

    if hashlib.sha256(code.encode('utf-8')).hexdigest() != otp.get('hash'):
        messages.error(request, 'Невірний код підтвердження.')
        if settings.DEBUG and otp.get('plain'):
            messages.info(request, f"TEST актуальний код: {otp.get('plain')}")
        return redirect('certificates_page')

    tx = otp.get('payment_tx')
    cp = CertificatePayment.objects.filter(transaction_id=tx, user=request.user).select_related('program').first()
    if not cp:
        messages.error(request, 'Платіж не знайдено.')
        return redirect('certificates_page')

    if cp.status != CertificatePayment.STATUS_SUCCESS:
        cp.status = CertificatePayment.STATUS_SUCCESS
        cp.paid_at = timezone.now()
        cp.save(update_fields=['status', 'paid_at'])
        program = cp.program or _get_or_create_program('a1')
        enrollment, _ = CertificateEnrollment.objects.get_or_create(
            user=request.user,
            program=program,
            defaults={'payment': cp, 'status': CertificateEnrollment.STATUS_ACTIVE},
        )
        if enrollment.payment_id != cp.id:
            enrollment.payment = cp
            enrollment.save(update_fields=['payment'])
    else:
        # Ensure enrollment exists even if payment already success
        program = cp.program or _get_or_create_program('a1')
        enrollment, _ = CertificateEnrollment.objects.get_or_create(
            user=request.user,
            program=program,
            defaults={'payment': cp, 'status': CertificateEnrollment.STATUS_ACTIVE},
        )
        if enrollment.payment_id != cp.id:
            enrollment.payment = cp
            enrollment.save(update_fields=['payment'])

    # receipt email (with referral code/link)
    to_email = (otp.get('contact') or '').strip()
    if to_email and _is_email(to_email):
        paid_at = cp.paid_at or timezone.now()
        ref = ReferralProfile.get_or_create_for_user(request.user)
        ref_code = ref.code
        ref_link = request.build_absolute_uri(f'/accounts/register/?ref={ref_code}')
        body = (
            "Квитанція / підтвердження оплати\n\n"
            "Тип: Сертифікат (підсумковий іспит)\n"
            f"Сума: {cp.amount_eur} €\n"
            f"Дата: {paid_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"Транзакція: {cp.transaction_id}\n\n"
            "Запроси друга і він отримає знижку 20% на Premium:\n"
            f"Промокод: {ref_code}\n"
            f"Посилання: {ref_link}\n\n"
            "Дякуємо за оплату."
        )
        ok, err = _send_receipt_email(to_email, 'Квитанція: Сертифікат оплачено', body)
        if not ok and settings.DEBUG:
            messages.info(request, f'Квитанцію не надіслано: {err}')

    if 'simple_cert_otp' in request.session:
        del request.session['simple_cert_otp']

    messages.success(request, 'Оплата підтверджена. Запит на сертифікат створено.')
    return redirect('certificates_page')


@login_required
def premium_checkout(request):
    if request.method != 'POST':
        return redirect('premium_page')

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if profile.is_premium:
        messages.info(request, 'У вас вже активний Premium.')
        return redirect('premium_page')

    if not settings.LIQPAY_PUBLIC_KEY or not settings.LIQPAY_PRIVATE_KEY:
        messages.error(request, 'LiqPay не налаштовано. Додайте ключі в settings.py.')
        return redirect('premium_page')

    try:
        period = int((request.POST.get('period_months') or '1').strip())
    except ValueError:
        period = 1
    if period not in (1, 3, 12):
        period = 1

    price_month_uah = 199
    ref = ReferralProfile.get_or_create_for_user(request.user)
    has_discount = bool(ref.referred_by_id and not ref.discount_used)
    amount_uah = int(price_month_uah * period * (0.8 if has_discount else 1))

    order_id = uuid.uuid4().hex[:20].upper()
    payment = PremiumPayment.objects.create(
        user=request.user,
        amount_uah=amount_uah,
        period_months=period,
        status=PremiumPayment.STATUS_PENDING,
        transaction_id=order_id,
    )
    if has_discount:
        ref.discount_used = True
        ref.save(update_fields=['discount_used'])

    payload = {
        'version': '3',
        'public_key': settings.LIQPAY_PUBLIC_KEY,
        'action': 'pay',
        'amount': str(payment.amount_uah),
        'currency': 'UAH',
        'description': f'Premium доступ до Lingua ({payment.period_months} міс.)',
        'order_id': payment.transaction_id,
        'server_url': request.build_absolute_uri('/accounts/premium/callback/'),
        'result_url': request.build_absolute_uri('/accounts/premium/result/'),
        'sandbox': '1' if settings.LIQPAY_SANDBOX else '0',
    }

    data = base64.b64encode(json.dumps(payload).encode('utf-8')).decode('utf-8')
    sign_string = f"{settings.LIQPAY_PRIVATE_KEY}{data}{settings.LIQPAY_PRIVATE_KEY}"
    signature = base64.b64encode(hashlib.sha1(sign_string.encode('utf-8')).digest()).decode('utf-8')

    return render(request, 'accounts/liqpay_redirect.html', {
        'data': data,
        'signature': signature,
        'liqpay_checkout_url': 'https://www.liqpay.ua/api/3/checkout',
    })


@login_required
def premium_manual_submit(request):
    if request.method != 'POST':
        return redirect('premium_page')

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if profile.is_premium:
        messages.info(request, 'У вас вже активний Premium.')
        return redirect('premium_page')

    try:
        period = int((request.POST.get('period_months') or '1').strip())
    except ValueError:
        period = 1
    if period not in (1, 3, 12):
        period = 1

    reference = (request.POST.get('reference') or '').strip()
    if len(reference) > 120:
        reference = reference[:120]

    price_month_uah = 199
    ref = ReferralProfile.get_or_create_for_user(request.user)
    has_discount = bool(ref.referred_by_id and not ref.discount_used)
    amount_uah = int(price_month_uah * period * (0.8 if has_discount else 1))

    internal_id = uuid.uuid4().hex[:20].upper()
    PremiumPayment.objects.create(
        user=request.user,
        amount_uah=amount_uah,
        period_months=period,
        reference=reference,
        status=PremiumPayment.STATUS_PENDING,
        transaction_id=internal_id,
    )
    if has_discount:
        ref.discount_used = True
        ref.save(update_fields=['discount_used'])
    messages.success(request, 'Заявку на Premium створено. Після перевірки ми активуємо доступ.')
    return redirect('premium_page')


@login_required
def premium_test_activate(request):
    """
    Local/dev shortcut: activates Premium without payment provider.
    Enabled only when DEBUG=True.
    """
    if not settings.DEBUG:
        messages.error(request, 'Ця дія доступна лише в тестовому режимі.')
        return redirect('premium_page')
    if request.method != 'POST':
        return redirect('premium_page')

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if profile.is_premium:
        messages.info(request, 'Premium уже активний.')
        return redirect('premium_page')

    try:
        period = int((request.POST.get('period_months') or '1').strip())
    except ValueError:
        period = 1
    if period not in (1, 3, 12):
        period = 1

    full_name = (request.POST.get('full_name') or '').strip()
    contact = (request.POST.get('contact') or '').strip()
    reference = (request.POST.get('reference') or '').strip()
    agree = request.POST.get('agree')
    code = (request.POST.get('otp_code') or '').strip()

    if not full_name or not contact or not reference or not agree:
        messages.error(request, 'Заповніть усі поля перед активацією.')
        return redirect('premium_page')

    otp = request.session.get('premium_otp') or {}
    if not otp.get('hash') or not otp.get('sent_at'):
        messages.error(request, 'Спочатку натисніть "Надіслати код".')
        return redirect('premium_page')

    if (contact.strip() != (otp.get('contact') or '').strip()) or (period != int(otp.get('period') or period)):
        messages.error(request, 'Дані змінилися. Надішліть код ще раз.')
        return redirect('premium_page')

    if not re.fullmatch(r'\d{6}', code or ''):
        messages.error(request, 'Введіть 6-значний код.')
        return redirect('premium_page')

    code_hash = hashlib.sha256(code.encode('utf-8')).hexdigest()
    if code_hash != otp.get('hash'):
        messages.error(request, 'Невірний код підтвердження.')
        return redirect('premium_page')

    # success: clear otp
    if 'premium_otp' in request.session:
        del request.session['premium_otp']

    if len(full_name) > 80:
        full_name = full_name[:80]
    if len(contact) > 80:
        contact = contact[:80]
    if len(reference) > 120:
        reference = reference[:120]

    price_month_uah = 199
    ref = ReferralProfile.get_or_create_for_user(request.user)
    has_discount = bool(ref.referred_by_id and not ref.discount_used)
    amount_uah = int(price_month_uah * period * (0.8 if has_discount else 1))

    internal_id = uuid.uuid4().hex[:20].upper()
    PremiumPayment.objects.create(
        user=request.user,
        amount_uah=amount_uah,
        period_months=period,
        reference=f'TEST_MODE | {full_name} | {contact} | {reference}',
        status=PremiumPayment.STATUS_SUCCESS,
        transaction_id=internal_id,
        paid_at=timezone.now(),
    )
    if has_discount:
        ref.discount_used = True
        ref.save(update_fields=['discount_used'])
    profile.is_premium = True
    profile.save(update_fields=['is_premium'])
    messages.success(request, 'Premium активовано (тестовий режим).')
    return redirect('premium_page')


@login_required
def certificates_page(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    simple_otp = request.session.get('simple_cert_otp') or {}
    simple_otp_contact = (simple_otp.get('contact') or '').strip()
    preselect_slug = (request.GET.get('buy') or '').strip().lower()

    programs = [
        _get_or_create_program('a1'),
        _get_or_create_program('a2'),
        _get_or_create_program('b1'),
        _get_or_create_program('b2'),
    ]
    program_cards = []
    for p in programs:
        enr = _get_enrollment(request.user, p)
        paid = _cert_is_paid(enr)
        state = _certificate_exam_state(request.user, p)
        program_cards.append({
            'program': p,
            'enrollment': enr,
            'paid': paid,
            'state': state,
        })
    return render(request, 'accounts/certificates.html', {
        'profile': profile,
        'price_eur': 25,
        'simple_otp_contact': simple_otp_contact,
        'programs': programs,
        'program_cards': program_cards,
        'preselect_slug': preselect_slug,
    })


@login_required
def certificate_exam_path(request, program_slug: str):
    program = _get_or_create_program(program_slug)
    enrollment = _get_enrollment(request.user, program)
    cert_paid = _cert_is_paid(enrollment)

    state = _certificate_exam_state(request.user, program)

    # When requirements met, allow generating a certificate issue with user-provided name.
    if request.method == 'POST':
        if not cert_paid:
            messages.error(request, 'Щоб згенерувати сертифікат, спочатку підтвердіть оплату.')
            return redirect('certificates_page')
        if not state['all_ok']:
            messages.error(request, 'Спочатку завершіть усі кроки.')
            return redirect('certificate_exam_path', program_slug=program.slug)
        full_name = (request.POST.get('full_name') or '').strip()
        if len(full_name) < 3:
            messages.error(request, 'Введіть імʼя та прізвище.')
            return redirect('certificate_exam_path', program_slug=program.slug)
        if len(full_name) > 120:
            full_name = full_name[:120]

        if not hasattr(enrollment, 'issue'):
            # create approved request for audit trail
            CertificateExamRequest.objects.get_or_create(
                user=request.user,
                status=CertificateExamRequest.STATUS_APPROVED,
                defaults={
                    'price_eur': 25,
                    'decided_at': timezone.now(),
                    'note': f"AUTO | lessons={state['completed_lessons']} | quiz={state['latest_quiz_percent']}%",
                },
            )
            cert_id = f"LSK-{enrollment.id:06d}"
            CertificateIssue.objects.create(
                enrollment=enrollment,
                full_name=full_name,
                certificate_id=cert_id,
            )
            enrollment.status = CertificateEnrollment.STATUS_COMPLETED
            enrollment.completed_at = timezone.now()
            enrollment.save(update_fields=['status', 'completed_at'])
        return redirect('certificate_document', program_slug=program.slug)

    issued = False
    req = CertificateExamRequest.objects.filter(user=request.user).order_by('-created_at').first()
    return render(request, 'accounts/certificate_exam_path.html', {
        'state': state,
        'request_obj': req,
        'issued': issued,
        'enrollment': enrollment,
        'program': program,
        'cert_paid': cert_paid,
    })


@login_required
def certificate_document(request, program_slug: str):
    program = _get_or_create_program(program_slug)
    enrollment = _get_enrollment(request.user, program)
    if not enrollment:
        messages.error(request, 'Немає доступу до сертифікації.')
        return redirect('certificates_page')

    state = _certificate_exam_state(request.user, program)
    issue = getattr(enrollment, 'issue', None)
    if not issue:
        messages.error(request, 'Спочатку завершіть програму і згенеруйте сертифікат.')
        return redirect('certificate_exam_path', program_slug=program.slug)

    display_name = issue.full_name
    cert_id = issue.certificate_id
    date_str = (issue.issued_at or timezone.now()).strftime('%d.%m.%Y')
    result_line = f"Успішно: {state['completed_lessons']}/{state['required_lessons']} уроків, тест {state['latest_quiz_percent']}%."

    return render(request, 'accounts/certificate_document.html', {
        'display_name': display_name,
        'cert_id': cert_id,
        'date_str': date_str,
        'result_line': result_line,
        'program': program,
        'default_email': _extract_contact_email_from_reference(getattr(getattr(enrollment, 'payment', None), 'reference', '') or ''),
    })


@login_required
def certificate_pdf(request, program_slug: str):
    program = _get_or_create_program(program_slug)
    enrollment = _get_enrollment(request.user, program)
    issue = getattr(enrollment, 'issue', None) if enrollment else None
    if not issue:
        messages.error(request, 'Сертифікат ще не згенеровано.')
        return redirect('certificate_exam_path', program_slug=program.slug)

    state = _certificate_exam_state(request.user, program)
    cert_id = issue.certificate_id
    date_str = (issue.issued_at or timezone.now()).strftime('%d.%m.%Y')
    result_line = f"Completed: {state['completed_lessons']}/{state['required_lessons']} lessons, test {state['latest_quiz_percent']}%."

    pdf_bytes = _build_certificate_pdf_bytes(
        cert_id=cert_id,
        date_str=date_str,
        program_title=program.title,
        program_level=program.level,
        full_name=issue.full_name,
        result_line=result_line,
    )
    filename = f"certificate_{program.slug}_{cert_id}.pdf"
    resp = HttpResponse(pdf_bytes, content_type='application/pdf')
    inline = (request.GET.get('inline') or '').strip() in ('1', 'true', 'yes')
    disp = 'inline' if inline else 'attachment'
    resp['Content-Disposition'] = f'{disp}; filename="{filename}"'
    return resp


@login_required
def certificate_email(request, program_slug: str):
    if request.method != 'POST':
        return redirect('certificate_document', program_slug=program_slug)

    program = _get_or_create_program(program_slug)
    enrollment = _get_enrollment(request.user, program)
    issue = getattr(enrollment, 'issue', None) if enrollment else None
    if not issue:
        messages.error(request, 'Сертифікат ще не згенеровано.')
        return redirect('certificate_exam_path', program_slug=program.slug)

    to_email = (request.POST.get('email') or '').strip()
    if not _is_email(to_email):
        messages.error(request, 'Введіть коректний email.')
        return redirect('certificate_document', program_slug=program.slug)

    state = _certificate_exam_state(request.user, program)
    cert_id = issue.certificate_id
    date_str = (issue.issued_at or timezone.now()).strftime('%d.%m.%Y')
    result_line = f"Completed: {state['completed_lessons']}/{state['required_lessons']} lessons, test {state['latest_quiz_percent']}%."

    pdf_bytes = _build_certificate_pdf_bytes(
        cert_id=cert_id,
        date_str=date_str,
        program_title=program.title,
        program_level=program.level,
        full_name=issue.full_name,
        result_line=result_line,
    )

    cfg = PaymentProviderConfig.get_solo()
    gmail_user = (getattr(settings, 'EMAIL_HOST_USER', '') or cfg.gmail_user or '').strip()
    gmail_pass = (getattr(settings, 'EMAIL_HOST_PASSWORD', '') or cfg.gmail_app_password or '').strip().replace(' ', '')
    if not (gmail_user and gmail_pass):
        messages.error(request, 'Email не налаштовано. Додайте Gmail логін/пароль в адмінці (Конфіг оплат/OTP).')
        return redirect('certificate_document', program_slug=program.slug)

    try:
        backend = EmailBackend(
            host='smtp.gmail.com',
            port=587,
            username=gmail_user,
            password=gmail_pass,
            use_tls=True,
            fail_silently=False,
        )
        msg = EmailMessage(
            subject=f"Сертифікат {program.level} — {cert_id}",
            body=(
                "Ваш сертифікат у вкладенні.\n\n"
                f"Програма: {program.title}\n"
                f"ID: {cert_id}\n"
                f"Дата: {date_str}\n\n"
                "Дякуємо, що навчаєтесь зі Slovak.sk"
            ),
            from_email=gmail_user,
            to=[to_email],
            connection=backend,
        )
        msg.attach(f"certificate_{program.slug}_{cert_id}.pdf", pdf_bytes, "application/pdf")
        msg.send(fail_silently=False)
        messages.success(request, 'Сертифікат надіслано на пошту.')
    except Exception as e:
        if settings.DEBUG:
            messages.error(request, f'Не вдалося надіслати: {type(e).__name__}: {e}')
        else:
            messages.error(request, 'Не вдалося надіслати сертифікат. Спробуйте ще раз.')
    return redirect('certificate_document', program_slug=program.slug)


@login_required
def certificate_request(request):
    if request.method != 'POST':
        return redirect('certificates_page')
    # prevent spam: only one pending at a time
    exists = CertificateExamRequest.objects.filter(user=request.user, status=CertificateExamRequest.STATUS_PENDING).exists()
    if exists:
        messages.info(request, 'Запит уже створено. Очікуйте підтвердження.')
        return redirect('certificates_page')
    CertificateExamRequest.objects.create(user=request.user, price_eur=25)
    messages.success(request, 'Запит на підсумковий іспит створено. Ми звʼяжемось з вами.')
    return redirect('certificates_page')


@login_required
def certificate_buy(request):
    if request.method != 'POST':
        return redirect('certificates_page')
    reference = (request.POST.get('reference') or '').strip()
    if len(reference) > 120:
        reference = reference[:120]

    internal_id = uuid.uuid4().hex[:20].upper()
    CertificatePayment.objects.create(
        user=request.user,
        amount_eur=25,
        reference=reference,
        status=CertificatePayment.STATUS_PENDING,
        transaction_id=internal_id,
    )
    messages.success(request, 'Заявку на оплату сертифікату створено. Після перевірки ми підтвердимо іспит/сертифікат.')
    return redirect('certificates_page')


def _process_liqpay_payload(data, signature):
    if not settings.LIQPAY_PRIVATE_KEY:
        return False, 'missing_private_key'

    expected = base64.b64encode(
        hashlib.sha1(f"{settings.LIQPAY_PRIVATE_KEY}{data}{settings.LIQPAY_PRIVATE_KEY}".encode('utf-8')).digest()
    ).decode('utf-8')
    if expected != signature:
        return False, 'invalid_signature'

    try:
        decoded = base64.b64decode(data).decode('utf-8')
        payload = json.loads(decoded)
    except Exception:
        return False, 'invalid_payload'

    order_id = payload.get('order_id')
    status = payload.get('status')
    if not order_id:
        return False, 'missing_order_id'

    payment = PremiumPayment.objects.filter(transaction_id=order_id).select_related('user').first()
    if not payment:
        return False, 'payment_not_found'

    if status in ('success', 'sandbox'):
        if payment.status != PremiumPayment.STATUS_SUCCESS:
            payment.status = PremiumPayment.STATUS_SUCCESS
            payment.paid_at = timezone.now()
            payment.save(update_fields=['status', 'paid_at'])
            profile, _ = UserProfile.objects.get_or_create(user=payment.user)
            if not profile.is_premium:
                profile.is_premium = True
                profile.save(update_fields=['is_premium'])
    elif status in ('failure', 'error', 'reversed'):
        if payment.status != PremiumPayment.STATUS_FAILED:
            payment.status = PremiumPayment.STATUS_FAILED
            payment.save(update_fields=['status'])

    return True, status


@csrf_exempt
def premium_liqpay_callback(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('POST only')

    data = request.POST.get('data', '')
    signature = request.POST.get('signature', '')
    ok, _ = _process_liqpay_payload(data, signature)
    if not ok:
        return HttpResponseBadRequest('Invalid callback')
    return redirect('premium_page')


@csrf_exempt
def premium_liqpay_result(request):
    if request.method == 'POST':
        data = request.POST.get('data', '')
        signature = request.POST.get('signature', '')
        ok, status = _process_liqpay_payload(data, signature)
        if ok and status in ('success', 'sandbox'):
            messages.success(request, 'Оплата успішна! Premium активовано.')
        elif ok:
            messages.warning(request, f'Оплата неуспішна. Статус: {status}')
        else:
            messages.error(request, 'Не вдалося перевірити відповідь від LiqPay.')
    return redirect('premium_page')