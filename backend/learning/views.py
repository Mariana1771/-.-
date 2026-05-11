from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count, Avg
from django.urls import reverse
from django.conf import settings
import random
import json
from urllib.parse import quote
from urllib.request import urlopen
import html

from .models import Lesson, Exercise, QuizQuestion, LessonProgress, QuizAttempt, UserProfile, PersonalWord

def get_or_create_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile

def has_lesson_access(user, lesson):
    # Free A1 is always доступний (even for guests).
    # Certification lessons (*_CERT) are gated by certificate payment for that level.
    if lesson.level == 'A1' and (lesson.course_tag or '') != 'A1_CERT':
        return True
    # A2 is free after registration (progress requires auth anyway).
    if lesson.level == 'A2' and not (lesson.course_tag or '').endswith('_CERT'):
        return bool(user and getattr(user, 'is_authenticated', False))
    if (lesson.course_tag or '').endswith('_CERT'):
        if not user.is_authenticated:
            return False
        try:
            from django.apps import apps
            CertificateEnrollment = apps.get_model('accounts', 'CertificateEnrollment')
            CertificatePayment = apps.get_model('accounts', 'CertificatePayment')
            CertificateProgram = apps.get_model('accounts', 'CertificateProgram')
            program = CertificateProgram.objects.filter(slug=lesson.level.lower()).first()
            if not program:
                return False
            enr = CertificateEnrollment.objects.filter(user=user, program=program).select_related('payment').first()
            return bool(enr and enr.payment and enr.payment.status == CertificatePayment.STATUS_SUCCESS)
        except Exception:
            return False
    if not user.is_authenticated:
        return False
    return get_or_create_profile(user).is_premium

# --------- ГОЛОВНА ТА ДЕШБОРД ---------
def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    features = [
        ('', 'Граматика', 'Рівні A1 → B2'),
        ('', 'Вправи', 'Після кожної теми'),
        ('', 'Тести', 'Перевір себе'),
        ('', 'Статистика', 'Твій прогрес'),
    ]
    start_a1_lesson = Lesson.objects.filter(level='A1', course_tag='').order_by('order', 'id').first()
    return render(request, 'learning/home.html', {
        'features': features,
        'start_a1_lesson': start_a1_lesson,
    })

@login_required
def dashboard(request):
    # Dashboard should focus on the main learning path (exclude CERT lessons).
    lessons = Lesson.objects.filter(course_tag='')
    profile = get_or_create_profile(request.user)
    if request.method == 'POST' and request.POST.get('action') == 'set_goal':
        def _clamp_int(value, default, min_v, max_v):
            try:
                v = int(value)
            except (TypeError, ValueError):
                return default
            return max(min_v, min(max_v, v))

        profile.daily_goal_lessons = _clamp_int(request.POST.get('goal_lessons'), profile.daily_goal_lessons, 1, 9)
        profile.daily_goal_minutes = _clamp_int(request.POST.get('goal_minutes'), profile.daily_goal_minutes, 5, 120)
        profile.daily_goal_words = _clamp_int(request.POST.get('goal_words'), profile.daily_goal_words, 3, 50)
        profile.save(update_fields=['daily_goal_lessons', 'daily_goal_minutes', 'daily_goal_words'])
        messages.success(request, 'Ціль оновлено.')
        return redirect('dashboard')
    completed_ids = set(
        LessonProgress.objects.filter(user=request.user, completed=True)
        .values_list('lesson_id', flat=True)
    )
    # Next lesson: first not-completed by curriculum order.
    next_lesson = lessons.exclude(id__in=completed_ids).order_by('level', 'order', 'id').first()
    recent_lessons = lessons.order_by('-id')[:4]
    context = {
        'lessons': recent_lessons,
        'completed_ids': completed_ids,
        'profile': profile,
        'total_lessons': lessons.count(),
        'next_lesson': next_lesson,
    }
    return render(request, 'learning/dashboard.html', context)

# --------- СПИСОК УРОКІВ ТА ДЕТАЛІ ---------
def grammar_list(request):
    if request.user.is_authenticated:
        profile = get_or_create_profile(request.user)
        completed_ids = set(LessonProgress.objects.filter(user=request.user, completed=True).values_list('lesson_id', flat=True))
    else:
        profile, completed_ids = None, set()

    premium_price_uah = 199
    context = {
        'a1_lessons': Lesson.objects.filter(level='A1', course_tag='').exclude(title__icontains='Словник').exclude(title__icontains='Текст').order_by('order', 'id'),
        'a2_lessons': Lesson.objects.filter(level='A2').exclude(title__icontains='Словник').exclude(title__icontains='Текст').order_by('order', 'id'),
        'b1_lessons': Lesson.objects.filter(level='B1').exclude(title__icontains='Словник').exclude(title__icontains='Текст').order_by('order', 'id'),
        'b2_lessons': Lesson.objects.filter(level='B2').exclude(title__icontains='Словник').exclude(title__icontains='Текст').order_by('order', 'id'),
        'completed_ids': completed_ids,
        'profile': profile,
        'has_premium': profile.is_premium if profile else False,
        'premium_price_uah': premium_price_uah,
        'premium_price_3m_uah': premium_price_uah * 3,
        'premium_price_year_uah': premium_price_uah * 12,
    }
    return render(request, 'learning/grammar_list.html', context)

def lesson_detail(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    if not has_lesson_access(request.user, lesson):
        if lesson.level == 'A1' and (lesson.course_tag or '') == 'A1_CERT':
            messages.warning(request, 'Цей курс доступний після оплати сертифікації.')
            return redirect('certificates_page')
        messages.warning(request, 'Цей рівень доступний лише з Premium. Безкоштовно доступний тільки рівень A1.')
        return redirect('grammar_list')
    # Отримуємо вправи для цього уроку
    exercises = Exercise.objects.filter(lesson=lesson).order_by('order', 'id')
    cert_program_slug = None
    if (lesson.course_tag or '').endswith('_CERT'):
        cert_program_slug = lesson.level.lower()
    return render(request, 'learning/lesson_detail.html', {
        'lesson': lesson,
        'exercises': exercises,
        'has_access': True,
        'cert_program_slug': cert_program_slug,
    })

# --------- ЛОГІКА ВПРАВ (EXERCISE) ---------
def exercise(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    if not has_lesson_access(request.user, lesson):
        messages.warning(request, 'Вправи цього рівня доступні лише з Premium.')
        return redirect('lesson_detail', lesson_id=lesson.id) if lesson.level == 'A1' else redirect('grammar_list')
    # Обмежуємо кількість вправ, щоб урок не був занадто довгим
    exercises = list(Exercise.objects.filter(lesson=lesson).order_by('order', 'id'))[:20]

    # Мінімум вправ на урок
    if len(exercises) < 8:
        messages.info(request, 'Для цієї теми ще недостатньо вправ (потрібно мінімум 8).')
        return redirect('lesson_detail', lesson_id=lesson_id)

    if not exercises:
        messages.info(request, 'У цього уроку ще немає вправ.')
        return redirect('lesson_detail', lesson_id=lesson_id)

    session_key = f'ex_index_{lesson_id}'
    session_score_key = f'ex_score_{lesson_id}'

    # Якщо це початок (GET запит без індексу в сесії)
    if request.method == 'GET' and session_key not in request.session:
        request.session[session_key] = 0
        request.session[session_score_key] = 0

    idx = request.session.get(session_key, 0)

    # helpers: options for choice or for "fill as choice"
    def _normalize(s: str) -> str:
        return str(s or '').strip().lower()

    def _get_or_build_options(ex: Exercise):
        """
        Returns a dict:
          { "opts": [..], "correct_idx": int }
        We always shuffle options (incl. TYPE_CHOICE) to make distractors less obvious.
        """
        # If options already set (choice exercises) - use them, but shuffle and compute correct_idx.
        base_opts = ex.get_options()
        if base_opts:
            # Determine correct text (from index or from text)
            ca_raw = str(ex.correct_answer or '').strip()
            correct_text = ''
            if ca_raw.isdigit():
                i = int(ca_raw)
                if 0 <= i < len(base_opts):
                    correct_text = str(base_opts[i])
            else:
                correct_text = str(ex.correct_answer or '').strip()

            opts = base_opts[:]
            random.shuffle(opts)
            correct_norm = _normalize(correct_text)
            try:
                correct_idx = next(i for i, t in enumerate(opts) if _normalize(t) == correct_norm)
            except StopIteration:
                correct_idx = -1
            return {"opts": opts, "correct_idx": correct_idx}

        # For fill exercises we generate 2 distractors from other answers in same lesson.
        correct = str(ex.correct_answer).strip()
        pool = []
        for e in exercises:
            if e.id == ex.id:
                continue
            a = str(e.correct_answer).strip()
            if a and a.lower() != correct.lower():
                pool.append(a)
        # unique, keep order
        uniq = []
        seen = set()
        for a in pool:
            k = a.lower()
            if k in seen:
                continue
            seen.add(k)
            uniq.append(a)

        # Prefer "confusing" distractors: most similar strings first
        try:
            import difflib
            scored = []
            for a in uniq:
                ratio = difflib.SequenceMatcher(a=_normalize(correct), b=_normalize(a)).ratio()
                # prefer same length-ish too
                len_penalty = abs(len(correct) - len(a)) / max(len(correct), 1)
                score = ratio - 0.15 * len_penalty
                scored.append((score, a))
            scored.sort(key=lambda t: t[0], reverse=True)
            distractors = [a for _, a in scored[:8]]
        except Exception:
            distractors = uniq[:]

        # If we still have few candidates, add tiny variants of the correct answer
        def _variants(s: str):
            v = []
            base = str(s).strip()
            if not base:
                return v
            low = _normalize(base)

            # Common verb confusions (A1)
            repl = [
                # byť
                (' som ', ' si '), (' som ', ' ste '), (' som ', ' je '), (' som ', ' sú '),
                (' si ', ' som '), (' si ', ' ste '), (' si ', ' je '),
                (' ste ', ' si '), (' ste ', ' som '), (' ste ', ' sú '),
                (' je ', ' som '), (' je ', ' sú '), (' je ', ' ste '),
                (' sú ', ' je '), (' sú ', ' sme '), (' sú ', ' ste '),
                (' sme ', ' ste '), (' sme ', ' sú '), (' sme ', ' som '),
                # mať
                (' mám', ' máš'), (' mám', ' má'), (' mám', ' máme'), (' mám', ' máte'),
                (' máš', ' mám'), (' máš', ' má'), (' máš', ' máte'),
                (' má ', ' mám '), (' má ', ' máš '), (' má ', ' majú '),
                # bývať
                (' bývam', ' bývaš'), (' bývam', ' býva'), (' bývam', ' bývame'),
                (' bývaš', ' bývam'), (' bývaš', ' býva'), (' bývaš', ' bývate'),
                (' býva ', ' bývam '), (' býva ', ' bývajú '),
                # ísť
                (' idem', ' ideš'), (' idem', ' ide'), (' idem', ' ideme'),
                (' ideš', ' idem'), (' ideš', ' idete'), (' ideš', ' ide'),
                (' ide ', ' idem '), (' ide ', ' idú '),
                # otázky
                ('kde', 'kedy'), ('kde', 'odkiaľ'), ('kde', 'ako'),
                ('kedy', 'kde'), ('odkiaľ', 'kde'), ('ako', 'čo'), ('čo', 'kto'), ('kto', 'čo'),
            ]

            # Apply replacements on lowercased string, then restore original casing minimally
            padded = f" {low} "
            for a, b in repl:
                if a in padded:
                    cand = padded.replace(a, b).strip()
                    if cand and cand != low:
                        v.append(cand)

            # Negation confusion
            if low.startswith('ne'):
                v.append(low[2:])
            else:
                v.append('ne' + low)

            # Replace 'z' with 'v' (common preposition mixup in A1 answers)
            v.append(low.replace(' z ', ' v '))
            v.append(low.replace(' v ', ' z '))

            # swap a word order for 2-word answers: "Som z Kyjeva" -> "Kyjeva som z"
            parts = base.split()
            if len(parts) == 2:
                v.append(parts[1] + " " + parts[0])
            elif len(parts) == 3:
                v.append(parts[1] + " " + parts[0] + " " + parts[2])
            # remove punctuation at end (common confusion)
            v.append(base.rstrip('?.!'))
            # lowercase/uppercase variant
            v.append(base.lower())
            # unique by normalize
            out = []
            sset = set()
            for x in v:
                nx = _normalize(x)
                if not nx or nx == _normalize(base) or nx in sset:
                    continue
                sset.add(nx)
                out.append(x)
            return out

        for vv in _variants(correct):
            if _normalize(vv) not in seen and _normalize(vv) != _normalize(correct):
                seen.add(_normalize(vv))
                distractors.append(vv)

        distractors = distractors[:]
        random.shuffle(distractors)
        distractors = distractors[:2]

        # Fallbacks if pool is too small
        while len(distractors) < 2:
            # generate more "confusing" options from the correct answer itself
            extra = [vv for vv in _variants(correct) if _normalize(vv) != _normalize(correct)]
            for vv in extra:
                if len(distractors) >= 2:
                    break
                if _normalize(vv) not in {_normalize(d) for d in distractors}:
                    distractors.append(vv)
            if len(distractors) < 2:
                distractors.append('—')

        opts = [correct, distractors[0], distractors[1]]
        random.shuffle(opts)
        correct_norm = _normalize(correct)
        try:
            correct_idx = next(i for i, t in enumerate(opts) if _normalize(t) == correct_norm)
        except StopIteration:
            correct_idx = -1
        return {"opts": opts, "correct_idx": correct_idx}

    options_session_key = f'ex_options_{lesson_id}'
    if options_session_key not in request.session:
        request.session[options_session_key] = {}

    if request.method == 'POST':
        current_ex = exercises[idx]
        correct_answer = _normalize(current_ex.correct_answer)

        # Skip (no score change, just advance)
        if request.POST.get('action') == 'skip':
            idx += 1
            request.session[session_key] = idx
            if idx >= len(exercises):
                final_score = request.session.get(session_score_key, 0)
                xp = final_score * 10
                if request.user.is_authenticated:
                    progress, _ = LessonProgress.objects.get_or_create(user=request.user, lesson=lesson)
                    if not progress.completed:
                        progress.completed = True
                        progress.completed_at = timezone.now()
                        progress.xp_earned = xp
                        progress.save()
                        profile = get_or_create_profile(request.user)
                        profile.total_xp += xp
                        profile.save()
                del request.session[session_key]
                del request.session[session_score_key]
                if options_session_key in request.session:
                    del request.session[options_session_key]
                return render(request, 'learning/exercise_done.html', {
                    'lesson': lesson, 'score': final_score, 'total': len(exercises), 'xp': xp
                })
            return redirect('exercise', lesson_id=lesson_id)

        # Determine if we show it as choice (either real choice or generated options for fill)
        stored = request.session.get(options_session_key, {}).get(str(current_ex.id))
        if not stored:
            stored = _get_or_build_options(current_ex)
            store = request.session.get(options_session_key, {})
            store[str(current_ex.id)] = stored
            request.session[options_session_key] = store

        options = stored.get("opts") if isinstance(stored, dict) else (stored or [])
        correct_idx = stored.get("correct_idx") if isinstance(stored, dict) else None
        is_choice = (current_ex.exercise_type == Exercise.TYPE_CHOICE) or bool(options)

        if is_choice:
            raw = request.POST.get('answer', '').strip()
            try:
                chosen_idx = int(raw)
            except ValueError:
                chosen_idx = -1

            if correct_idx is not None and correct_idx >= 0:
                is_correct = (chosen_idx == int(correct_idx))
            else:
                # Backward/forward compatible: allow correct_answer to be either index ("0/1/2") or text
                chosen_text = _normalize(options[chosen_idx]) if 0 <= chosen_idx < len(options) else ''
                is_correct = (raw == correct_answer) or (chosen_text == correct_answer)
        else:
            user_answer = _normalize(request.POST.get('answer', ''))
            is_correct = (user_answer == correct_answer)

        if is_correct:
            request.session[session_score_key] = request.session.get(session_score_key, 0) + 1

        # Перехід до наступного питання
        idx += 1
        request.session[session_key] = idx

        # Якщо вправи закінчилися
        if idx >= len(exercises):
            final_score = request.session.get(session_score_key, 0)
            xp = final_score * 10

            if request.user.is_authenticated:
                progress, _ = LessonProgress.objects.get_or_create(user=request.user, lesson=lesson)
                if not progress.completed:
                    progress.completed = True
                    progress.completed_at = timezone.now()
                    progress.xp_earned = xp
                    progress.save()
                    profile = get_or_create_profile(request.user)
                    profile.total_xp += xp
                    profile.save()

            # Очищення сесії
            del request.session[session_key]
            del request.session[session_score_key]
            if options_session_key in request.session:
                del request.session[options_session_key]

            return render(request, 'learning/exercise_done.html', {
                'lesson': lesson, 'score': final_score, 'total': len(exercises), 'xp': xp
            })
        
        return redirect('exercise', lesson_id=lesson_id)

    # Відображення поточної вправи
    ex = exercises[idx]
    stored = request.session.get(options_session_key, {}).get(str(ex.id))
    if not stored:
        stored = _get_or_build_options(ex)
        store = request.session.get(options_session_key, {})
        store[str(ex.id)] = stored
        request.session[options_session_key] = store

    options = stored.get("opts") if isinstance(stored, dict) else (stored or [])
    is_choice = (ex.exercise_type == Exercise.TYPE_CHOICE) or bool(options)

    return render(request, 'learning/exercise.html', {
        'lesson': lesson,
        'ex': ex,
        'idx': idx,
        'total': len(exercises),
        'options': options if is_choice else [],
        'is_choice': is_choice,
    })

# --------- ТЕСТИ (QUIZ) ---------
def quiz(request):
    final_level = (request.GET.get('level') or '').strip().upper()
    is_final = (request.GET.get('final') or '').strip() in ('1', 'true', 'yes')
    if is_final and final_level:
        if not request.user.is_authenticated:
            messages.error(request, 'Увійдіть, щоб пройти фінальний тест.')
            return redirect('login')
        # Gate final exam behind certificate payment (A1 program content is free).
        if final_level in ('A1', 'A2', 'B1', 'B2'):
            try:
                from django.apps import apps
                CertificateEnrollment = apps.get_model('accounts', 'CertificateEnrollment')
                CertificatePayment = apps.get_model('accounts', 'CertificatePayment')
                CertificateProgram = apps.get_model('accounts', 'CertificateProgram')
                program = CertificateProgram.objects.filter(slug=final_level.lower()).first()
                if not program:
                    messages.error(request, 'Сертифікація поки недоступна.')
                    return redirect('certificates_page')
                enr = CertificateEnrollment.objects.filter(user=request.user, program=program).select_related('payment').first()
                if not enr or not enr.payment or enr.payment.status != CertificatePayment.STATUS_SUCCESS:
                    messages.error(request, 'Щоб пройти фінальний іспит, потрібно підтвердити оплату сертифікату.')
                    return redirect('certificates_page')
            except Exception:
                # If anything goes wrong, fail closed.
                messages.error(request, 'Не вдалося перевірити доступ до іспиту. Спробуйте ще раз.')
                return redirect('certificates_page')

    if request.method == 'POST':
        # Отримуємо ID питань, які були в цьому тесті
        question_ids = request.session.get('quiz_question_ids', [])
        qs = list(QuizQuestion.objects.filter(id__in=question_ids))
        by_id = {q.id: q for q in qs}
        questions = [by_id[qid] for qid in question_ids if qid in by_id]
        
        # Рахуємо правильні відповіді
        score = 0
        review = []
        for q in questions:
            user_ans = request.POST.get(f'q_{q.id}')
            try:
                user_idx = int(user_ans) if user_ans is not None else None
            except (TypeError, ValueError):
                user_idx = None

            is_correct = (user_idx is not None and user_idx == int(q.correct_index))
            if is_correct:
                score += 1
            opts = q.get_options()
            review.append({
                'id': q.id,
                'level': q.level,
                'question': q.question,
                'options': opts,
                'correct_index': int(q.correct_index),
                'your_index': user_idx,
                'is_correct': is_correct,
                'correct_text': opts[int(q.correct_index)] if 0 <= int(q.correct_index) < len(opts) else '',
                'your_text': opts[user_idx] if user_idx is not None and 0 <= user_idx < len(opts) else '—',
            })
        
        # Створюємо запис про спробу
        attempt = QuizAttempt.objects.create(
            user=request.user if request.user.is_authenticated else None,
            level=final_level if final_level in ('A1', 'A2', 'B1', 'B2') else '',
            is_final=bool(is_final and final_level in ('A1', 'A2', 'B1', 'B2')),
            score=score,
            total=len(questions),
            xp_earned=score * 20
        )
        
        # Нараховуємо XP, якщо користувач авторизований
        if request.user.is_authenticated:
            profile = get_or_create_profile(request.user)
            profile.total_xp += attempt.xp_earned
            profile.save()
            
        # Зберігаємо ID спроби, щоб показати результат на наступній сторінці
        request.session['last_quiz_id'] = attempt.id
        request.session['last_quiz_review'] = review
        
        # Очищаємо список питань з сесії, щоб тест не "зациклився"
        if 'quiz_question_ids' in request.session:
            del request.session['quiz_question_ids']
            
        return redirect('quiz_result')

    # GET запит: підготовка нових питань
    qset = QuizQuestion.objects.all()
    if final_level in ('A1', 'A2', 'B1', 'B2'):
        qset = qset.filter(level=final_level)

    all_q = list(qset)
    if not all_q:
        messages.warning(request, "У базі ще немає питань для тестів.")
        return redirect('dashboard')
        
    # Вибираємо 6 випадкових питань (або менше, якщо в базі мало)
    questions = random.sample(all_q, min(6, len(all_q)))
    request.session['quiz_question_ids'] = [q.id for q in questions]
    
    return render(request, 'learning/quiz.html', {
        'questions': questions,
        'final_level': final_level if final_level in ('A1', 'A2', 'B1', 'B2') else '',
        'is_final': bool(is_final and final_level in ('A1', 'A2', 'B1', 'B2')),
    })

def quiz_result(request):
    # Дістаємо ID останньої спроби
    attempt_id = request.session.get('last_quiz_id')
    
    if not attempt_id:
        # Якщо людина зайшла на сторінку результату просто так - повертаємо на тест
        return redirect('quiz')
        
    attempt = get_object_or_404(QuizAttempt, id=attempt_id)
    
    review = request.session.get('last_quiz_review', [])

    return render(request, 'learning/quiz_result.html', {
        'attempt': attempt,
        'review': review,
        'cert_program_slug': attempt.level.lower() if attempt.is_final and attempt.level in ('A1', 'A2', 'B1', 'B2') else '',
    })

# --------- СТАТИСТИКА ТА ІНШЕ ---------
@login_required
def stats(request):
    profile = get_or_create_profile(request.user)
    progress_qs = LessonProgress.objects.filter(user=request.user, completed=True)
    quiz_attempts = QuizAttempt.objects.filter(user=request.user)
    avg_quiz = quiz_attempts.aggregate(Avg('score'))['score__avg'] or 0

    all_lessons = Lesson.objects.all()
    completed_ids = set(progress_qs.values_list('lesson_id', flat=True))
    quiz_count = quiz_attempts.count()
    avg_quiz_pct = round(avg_quiz / 6 * 100) if quiz_attempts.exists() else 0
    completion_pct = round((progress_qs.count() / all_lessons.count() * 100), 1) if all_lessons.exists() else 0

    # Bars for small "chart" (newest -> oldest, up to 7)
    attempt_bars = []
    for a in quiz_attempts.order_by('-taken_at')[:7]:
        attempt_bars.append({
            'pct': a.percent,
            'label': a.taken_at.strftime('%d.%m'),
            'score': f'{a.score}/{a.total}',
        })

    return render(request, 'learning/stats.html', {
        'profile': profile,
        'progress_list': progress_qs,
        'quiz_attempts': quiz_attempts.order_by('-taken_at')[:10],
        'total_lessons': all_lessons.count(),
        'completed_count': progress_qs.count(),
        'avg_quiz_pct': avg_quiz_pct,
        'quiz_count': quiz_count,
        'all_lessons': all_lessons,
        'completed_ids': completed_ids,
        'completion_pct': completion_pct,
        'attempt_bars': attempt_bars,
    })

def dictionary(request):
    personal_words = []
    if request.user.is_authenticated:
        personal_words = PersonalWord.objects.filter(user=request.user)[:100]
    return render(request, 'learning/dictionary.html', {
        'lessons': Lesson.objects.filter(title__icontains='Словник'),
        'personal_words': personal_words,
    })

def texts(request):
    return render(request, 'learning/texts.html', {'texts': Lesson.objects.filter(title__icontains='Текст')})

def alphabet(request):
    return render(request, 'learning/alphabet.html')


def text_reader(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, title__icontains='Текст')
    return render(request, 'learning/text_reader.html', {'lesson': lesson})


@require_POST
def translate_word(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Некоректні дані.'}, status=400)

    word = (payload.get('word') or '').strip()
    if not word:
        return JsonResponse({'ok': False, 'error': 'Слово порожнє.'}, status=400)
    if len(word) > 60:
        return JsonResponse({'ok': False, 'error': 'Слово занадто довге.'}, status=400)

    translation = ''
    alternatives: list[str] = []

    def _clean_text(value):
        return html.unescape((value or '').strip())

    def _has_cyrillic(s: str) -> bool:
        # Ukrainian/Russian letters range (rough check)
        for ch in s:
            o = ord(ch)
            if 0x0400 <= o <= 0x04FF:
                return True
        return False

    # If user selected Ukrainian text by mistake, auto-swap direction.
    sl, tl = ('uk', 'sk') if _has_cyrillic(word) else ('sk', 'uk')
    try:
        # Google endpoint usually gives better quality for single words.
        # Add dt=bd to get dictionary-like suggestions when available.
        url = (
            "https://translate.googleapis.com/translate_a/single"
            f"?client=gtx&sl={sl}&tl={tl}&dt=t&dt=bd&dt=rm&q={quote(word)}"
        )
        with urlopen(url, timeout=4) as response:
            data = json.loads(response.read().decode('utf-8'))
            parts = data[0] if isinstance(data, list) and data else []
            translation = _clean_text(''.join([p[0] for p in parts if isinstance(p, list) and p]) if parts else '')
            alternatives = [_clean_text(p[0]) for p in parts if isinstance(p, list) and p and p[0]]

            # Dictionary suggestions: data[1] can contain parts of speech with "terms"
            try:
                dict_blocks = data[1] if isinstance(data, list) and len(data) > 1 else None
                if isinstance(dict_blocks, list):
                    for blk in dict_blocks[:4]:
                        if not isinstance(blk, dict):
                            continue
                        terms = blk.get('terms') or []
                        for t in terms[:6]:
                            ct = _clean_text(t)
                            if ct:
                                alternatives.append(ct)
            except Exception:
                pass
    except Exception:
        translation = ''

    # Fallback source if Google endpoint is unavailable.
    if not translation:
        try:
            url = f"https://api.mymemory.translated.net/get?q={quote(word)}&langpair={sl}|{tl}"
            with urlopen(url, timeout=4) as response:
                data = json.loads(response.read().decode('utf-8'))
                translation = _clean_text((data.get('responseData') or {}).get('translatedText') or '')
                matches = data.get('matches') or []
                for item in matches[:5]:
                    cand = _clean_text(item.get('translation', ''))
                    if cand:
                        alternatives.append(cand)
        except Exception:
            translation = ''

    # If service returned the original word unchanged, try first alternative.
    if translation and translation.lower() == word.lower():
        for cand in alternatives:
            if cand and cand.lower() != word.lower():
                translation = cand
                break

    if not translation:
        translation = 'Переклад не знайдено'

    # De-duplicate alternatives while preserving order
    seen = set()
    uniq: list[str] = []
    for a in alternatives:
        k = (a or '').strip().lower()
        if not k or k in seen:
            continue
        seen.add(k)
        uniq.append(a)

    return JsonResponse({'ok': True, 'word': word, 'translation': translation, 'alternatives': uniq[:5]})


@require_POST
def add_personal_word(request):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'Потрібно увійти в акаунт.'}, status=401)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Некоректні дані.'}, status=400)

    word = (payload.get('word') or '').strip()
    translation = (payload.get('translation') or '').strip()

    if not word or not translation:
        return JsonResponse({'ok': False, 'error': 'Заповніть слово та переклад.'}, status=400)

    obj, created = PersonalWord.objects.get_or_create(
        user=request.user,
        source_word=word.lower(),
        defaults={'translated_word': translation}
    )
    if not created:
        obj.translated_word = translation
        obj.save(update_fields=['translated_word'])
        return JsonResponse({'ok': True, 'created': False, 'message': 'Слово оновлено у словнику.'})

    return JsonResponse({'ok': True, 'created': True, 'message': 'Слово додано у словник.'})

# --------- ТЕСТ ВИЗНАЧЕННЯ РІВНЯ ---------
def placement_result(request):
    """
    Result page for placement test.
    Guests are redirected to registration; result is shown after auth.
    """
    payload = request.session.get('placement_result_payload') or {}
    if not payload:
        return redirect('placement_test')

    if not request.user.is_authenticated:
        messages.info(request, 'Щоб переглянути результат — зареєструйся або увійди.')
        return redirect(f"{reverse('register')}?next={quote(reverse('placement_result'))}")

    # Clear payload after successful view (prevent showing stale results later)
    try:
        del request.session['placement_result_payload']
    except Exception:
        pass

    determined_level = (payload.get('determined_level') or 'A1').strip()
    start_lesson_id = payload.get('start_lesson_id')
    start_lesson = Lesson.objects.filter(id=start_lesson_id).first() if start_lesson_id else None

    return render(request, 'learning/placement_result.html', {
        'determined_level': determined_level,
        'recommendation': payload.get('recommendation') or '',
        'start_lesson': start_lesson,
        'a1_pct': payload.get('a1_pct', 0),
        'a2_pct': payload.get('a2_pct', 0),
        'b1_pct': payload.get('b1_pct', 0),
        'b2_pct': payload.get('b2_pct', 0),
        'mistakes': payload.get('mistakes', []),
    })


def placement_test(request):
    from .models import PlacementQuestion
    # Auto-seed minimal placement questions in dev/demo environments.
    if PlacementQuestion.objects.count() == 0 and getattr(settings, 'DEBUG', False):
        seed = [
            # A1 (5)
            ('A1', 'Ako sa voláš?', 'Volám sa Anna.', 'Mám 20 rokov.', 'Bývam doma.', 0),
            ('A1', 'Doplň: Ja ___ študent.', 'som', 'si', 'je', 0),
            ('A1', 'Doplň: Ty ___ z Ukrajiny.', 'som', 'si', 'je', 1),
            ('A1', 'Vyber správne: Mám ___ knihu.', 'jeden', 'jednu', 'jedno', 1),
            ('A1', 'Čo je to? (stôl)', 'table', 'chair', 'door', 0),
            # A2 (5)
            ('A2', 'Doplň: Včera som ___ do práce.', 'idem', 'išiel', 'pôjdem', 1),
            ('A2', 'Vyber správne: Zajtra ___ na výlet.', 'pôjdem', 'išiel', 'chodím', 0),
            ('A2', 'Doplň: Nemám čas, ___ sa učím.', 'pretože', 'ale', 'takže', 0),
            ('A2', 'Ktorá veta je správna?', 'Vždy pijem kávy.', 'Vždy pijem kávu.', 'Vždy pijem káva.', 1),
            ('A2', 'Doplň: Páči sa mi ___ film.', 'tento', 'táto', 'tieto', 0),
            # B1 (5)
            ('B1', 'Vyber správne: Keby som mal viac času, ___ by som viac.', 'učím sa', 'učil by som sa', 'učil som sa', 1),
            ('B1', 'Ktorá veta je najprirodzenejšia?', 'Včera som sa stretol s kamarátom.', 'Včera som sa stretnúť s kamarátom.', 'Včera som sa stretol kamarát.', 0),
            ('B1', 'Doplň: Myslím si, že to ___ dobrý nápad.', 'je', 'bol', 'budem', 0),
            ('B1', 'Vyber synonymum k „dôležitý“', 'lacný', 'podstatný', 'špinavý', 1),
            ('B1', 'Doplň: Už som to urobil, ___ sa neboj.', 'tak', 'preto', 'aby', 0),
            # B2 (5)
            ('B2', 'Vyber správne: Aj keď som bol unavený, ___ som pracoval ďalej.', 'predsa', 'nikdy', 'len', 0),
            ('B2', 'Ktorá veta je správna?', 'Napriek tomu, že pršalo, išli sme von.', 'Napriek tomu pršalo, išli sme von.', 'Napriek že pršalo, išli sme von.', 0),
            ('B2', 'Vyber význam: „zvážiť“', 'zabudnúť', 'premyslieť', 'zjesť', 1),
            ('B2', 'Vyber správne: Ak by si mi to povedal skôr, ___ by sme to vyriešili.', 'mohli', 'môžeme', 'mohli sme', 2),
            ('B2', 'Doplň: Je to otázka, ___ sa nedá odpovedať jednoducho.', 'na ktorú', 'ktorý', 'kto', 0),
        ]
        objs = []
        order = 1
        for lvl, q, a, b, c, corr in seed:
            objs.append(PlacementQuestion(
                level=lvl,
                question=q,
                option_a=a,
                option_b=b,
                option_c=c,
                correct_index=int(corr),
                order=order,
            ))
            order += 1
        PlacementQuestion.objects.bulk_create(objs)

    if request.method == 'POST':
        question_ids = request.session.get('placement_ids', [])
        questions = PlacementQuestion.objects.filter(id__in=question_ids)
        level_scores = {'A1': 0, 'A2': 0, 'B1': 0, 'B2': 0}
        level_totals = {'A1': 0, 'A2': 0, 'B1': 0, 'B2': 0}
        mistakes = []
        for q in questions:
            level_totals[q.level] = level_totals.get(q.level, 0) + 1
            user_ans = request.POST.get(f'q_{q.id}')
            if user_ans == str(q.correct_index):
                level_scores[q.level] = level_scores.get(q.level, 0) + 1
            else:
                opts = q.get_options()
                try:
                    user_idx = int(user_ans) if user_ans is not None else None
                except (TypeError, ValueError):
                    user_idx = None
                mistakes.append({
                    'level': q.level,
                    'question': q.question,
                    'correct': opts[q.correct_index] if 0 <= q.correct_index < len(opts) else '',
                    'your': opts[user_idx] if user_idx is not None and 0 <= user_idx < len(opts) else '—',
                })

        def pct(lvl):
            t = level_totals.get(lvl, 0)
            return (level_scores.get(lvl, 0) / t * 100) if t > 0 else 0

        if pct('B2') >= 60:
            determined_level = 'B2'
            recommendation = 'Вище середнього рівень'
        elif pct('B1') >= 60:
            determined_level = 'B1'
            recommendation = 'Середній рівень'
        elif pct('A2') >= 60:
            determined_level = 'A2'
            recommendation = 'Базовий рівень'
        else:
            determined_level = 'A1'
            recommendation = 'Початковий рівень'

        start_lesson = Lesson.objects.filter(level=determined_level).order_by('order').first()
        if request.user.is_authenticated:
            profile = get_or_create_profile(request.user)
            profile.save()
        if 'placement_ids' in request.session:
            del request.session['placement_ids']

        # Store result in session so we can show it after auth (or immediately for logged in users).
        request.session['placement_result_payload'] = {
            'determined_level': determined_level,
            'recommendation': recommendation,
            'start_lesson_id': start_lesson.id if start_lesson else None,
            'a1_pct': round(pct('A1')),
            'a2_pct': round(pct('A2')),
            'b1_pct': round(pct('B1')),
            'b2_pct': round(pct('B2')),
            'mistakes': mistakes,
        }

        if not request.user.is_authenticated:
            messages.info(request, 'Тест завершено. Зареєструйся або увійди, щоб переглянути результат.')
            return redirect(f"{reverse('register')}?next={quote(reverse('placement_result'))}")

        return redirect('placement_result')

    from .models import PlacementQuestion
    # Build sections in Python to keep template simple (no complex slice/first logic).
    levels = ['A1', 'A2', 'B1', 'B2']
    sections: list[dict] = []
    picked_ids: list[int] = []
    n = 1
    for level in levels:
        pool = list(PlacementQuestion.objects.filter(level=level).order_by('order', 'id'))
        if not pool:
            continue
        picked = random.sample(pool, min(5, len(pool)))
        items = []
        for q in picked:
            items.append({'obj': q, 'num': n})
            picked_ids.append(q.id)
            n += 1
        sections.append({'level': level, 'items': items})

    if not picked_ids:
        messages.warning(request, 'Питання для тесту ще не додані. Зверніться до адміністратора.')
        return redirect('home')

    request.session['placement_ids'] = picked_ids
    total_questions = len(picked_ids)
    return render(request, 'learning/placement_test.html', {
        'sections': sections,
        'total_questions': total_questions,
    })


# --------- ОСОБИСТИЙ СЛОВНИК (legacy route) ---------
def my_words(request):
    # залишаємо маршрут для сумісності, але використовуємо єдиний словник
    return redirect('dictionary')


@require_POST
def add_word(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Потрібна авторизація'}, status=401)
    try:
        data = json.loads(request.body)
        slovak = (data.get('slovak') or '').strip()
        ukrainian = (data.get('ukrainian') or '').strip()
        if not slovak or not ukrainian:
            return JsonResponse({'error': 'Заповніть слово та переклад'}, status=400)
        word, created = PersonalWord.objects.get_or_create(
            user=request.user,
            source_word=slovak.lower(),
            defaults={'translated_word': ukrainian}
        )
        return JsonResponse({'status': 'added' if created else 'exists',
                             'message': 'Додано!' if created else 'Вже є у словнику'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def toggle_learned(request, word_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Потрібна авторизація'}, status=401)
    word = get_object_or_404(PersonalWord, id=word_id, user=request.user)
    return JsonResponse({'status': 'ok', 'learned': False})


@require_POST
def delete_word(request, word_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Потрібна авторизація'}, status=401)
    word = get_object_or_404(PersonalWord, id=word_id, user=request.user)
    word.delete()
    return JsonResponse({'status': 'deleted'})
