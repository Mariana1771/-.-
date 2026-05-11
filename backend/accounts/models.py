from django.db import models
from django.contrib.auth.models import User
import secrets
from learning.models import Lesson


class PaymentProviderConfig(models.Model):
    """
    Stores SMTP/SMS credentials in DB so the owner can edit them in admin
    without sharing secrets in chat or committing them to git.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    gmail_user = models.EmailField(blank=True, default='')
    gmail_app_password = models.CharField(max_length=128, blank=True, default='')
    turbosms_token = models.CharField(max_length=256, blank=True, default='')
    turbosms_sender = models.CharField(max_length=25, blank=True, default='TurboSMS')

    class Meta:
        verbose_name = 'Конфіг оплат/OTP'
        verbose_name_plural = 'Конфіг оплат/OTP'

    def __str__(self):
        return 'PaymentProviderConfig'

    @classmethod
    def get_solo(cls):
        # Prefer the newest configured record (people sometimes click "Add" twice).
        configured = cls.objects.exclude(gmail_user='').order_by('-id').first()
        if configured:
            return configured
        configured_sms = cls.objects.exclude(turbosms_token='').order_by('-id').first()
        if configured_sms:
            return configured_sms
        obj = cls.objects.order_by('-id').first()
        if obj:
            return obj
        return cls.objects.create()


class ReferralProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='referral')
    code = models.CharField(max_length=12, unique=True, db_index=True)
    referred_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='referrals')
    discount_used = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Реферальний профіль'
        verbose_name_plural = 'Реферальні профілі'

    def __str__(self):
        return f'{self.user.username} ({self.code})'

    @staticmethod
    def generate_code():
        # url-safe, short
        return secrets.token_urlsafe(6).replace('-', '').replace('_', '')[:10].upper()

    @classmethod
    def get_or_create_for_user(cls, user: User):
        obj = getattr(user, 'referral', None)
        if obj:
            return obj
        # Ensure unique code
        for _ in range(10):
            code = cls.generate_code()
            if not cls.objects.filter(code=code).exists():
                return cls.objects.create(user=user, code=code)
        return cls.objects.create(user=user, code=cls.generate_code())


class CertificateExamRequest(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Очікує'),
        (STATUS_APPROVED, 'Підтверджено'),
        (STATUS_REJECTED, 'Відхилено'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificate_requests')
    price_eur = models.PositiveSmallIntegerField(default=25)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    note = models.CharField(max_length=200, blank=True, default='')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Запит на сертифікат'
        verbose_name_plural = 'Запити на сертифікат'

    def __str__(self):
        return f'{self.user.username} - {self.status}'


class CertificatePayment(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Очікує'),
        (STATUS_SUCCESS, 'Успішно'),
        (STATUS_FAILED, 'Помилка'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificate_payments')
    program = models.ForeignKey('CertificateProgram', null=True, blank=True, on_delete=models.SET_NULL, related_name='payments')
    amount_eur = models.PositiveSmallIntegerField(default=25, verbose_name='Сума (€)')
    reference = models.CharField(max_length=120, blank=True, default='', verbose_name='Референс/коментар')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    transaction_id = models.CharField(max_length=40, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Оплата сертифікату'
        verbose_name_plural = 'Оплати сертифікату'

    def __str__(self):
        return f'{self.user.username} - {self.amount_eur}€ - {self.status}'


class CertificateProgram(models.Model):
    """
    Product wrapper for certification: defines what user buys and what must be completed.
    MVP: A1 only.
    """

    slug = models.SlugField(max_length=40, unique=True)
    title = models.CharField(max_length=120)
    level = models.CharField(max_length=2, default='A1')
    short_pitch = models.CharField(max_length=240, blank=True, default='')
    description_html = models.TextField(blank=True, default='')

    # Requirements (MVP, simple fields instead of JSON)
    required_lessons_percent = models.PositiveSmallIntegerField(default=80)
    required_quiz_percent = models.PositiveSmallIntegerField(default=70)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Програма сертифікації'
        verbose_name_plural = 'Програми сертифікації'

    def __str__(self):
        return f'{self.title} ({self.level})'


class CertificateEnrollment(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_COMPLETED = 'completed'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Активна'),
        (STATUS_COMPLETED, 'Завершена'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificate_enrollments')
    program = models.ForeignKey(CertificateProgram, on_delete=models.CASCADE, related_name='enrollments')
    payment = models.ForeignKey(CertificatePayment, null=True, blank=True, on_delete=models.SET_NULL, related_name='enrollments')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'program')
        verbose_name = 'Запис на сертифікацію'
        verbose_name_plural = 'Записи на сертифікацію'

    def __str__(self):
        return f'{self.user.username} → {self.program.slug} ({self.status})'


class CertificateIssue(models.Model):
    """
    Issued certificate document data (user-provided full name).
    """

    enrollment = models.OneToOneField(CertificateEnrollment, on_delete=models.CASCADE, related_name='issue')
    full_name = models.CharField(max_length=120)
    certificate_id = models.CharField(max_length=20, unique=True, db_index=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Виданий сертифікат'
        verbose_name_plural = 'Видані сертифікати'

    def __str__(self):
        return f'{self.certificate_id} — {self.full_name}'


class CertificateProgramLesson(models.Model):
    """
    Explicit course curriculum for certification program (ordered).
    This makes A1 certification feel like a real standalone course.
    """

    program = models.ForeignKey(CertificateProgram, on_delete=models.CASCADE, related_name='program_lessons')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('program', 'lesson')
        ordering = ['order', 'id']
        verbose_name = 'Урок програми сертифікації'
        verbose_name_plural = 'Уроки програм сертифікації'

    def __str__(self):
        return f'{self.program.slug}: {self.lesson}'

