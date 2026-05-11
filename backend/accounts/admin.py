from django.contrib import admin
from django.utils import timezone
from learning.models import UserProfile
from .models import (
    PaymentProviderConfig,
    ReferralProfile,
    CertificateExamRequest,
    CertificatePayment,
    CertificateProgram,
    CertificateEnrollment,
    CertificateIssue,
    CertificateProgramLesson,
)


@admin.register(PaymentProviderConfig)
class PaymentProviderConfigAdmin(admin.ModelAdmin):
    list_display = ('id', 'gmail_user', 'has_gmail_password', 'has_turbosms_token', 'turbosms_sender', 'updated_at')

    def has_gmail_password(self, obj: PaymentProviderConfig):
        return bool(obj.gmail_app_password)

    def has_turbosms_token(self, obj: PaymentProviderConfig):
        return bool(obj.turbosms_token)

    has_gmail_password.boolean = True
    has_gmail_password.short_description = 'Gmail пароль'
    has_turbosms_token.boolean = True
    has_turbosms_token.short_description = 'TurboSMS токен'


@admin.register(ReferralProfile)
class ReferralProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'referred_by', 'discount_used')
    search_fields = ('user__username', 'code', 'referred_by__username')
    list_filter = ('discount_used',)


@admin.register(CertificateExamRequest)
class CertificateExamRequestAdmin(admin.ModelAdmin):
    actions = ('approve', 'reject')
    list_display = ('user', 'price_eur', 'status', 'created_at', 'decided_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username',)

    @admin.action(description='Підтвердити')
    def approve(self, request, queryset):
        queryset.update(status=CertificateExamRequest.STATUS_APPROVED, decided_at=timezone.now())
        self.message_user(request, f'Підтверджено: {queryset.count()}')

    @admin.action(description='Відхилити')
    def reject(self, request, queryset):
        queryset.update(status=CertificateExamRequest.STATUS_REJECTED, decided_at=timezone.now())
        self.message_user(request, f'Відхилено: {queryset.count()}')


@admin.register(CertificatePayment)
class CertificatePaymentAdmin(admin.ModelAdmin):
    actions = ('mark_success',)
    list_display = ('user', 'amount_eur', 'status', 'reference', 'transaction_id', 'created_at', 'paid_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'transaction_id', 'reference')

    @admin.action(description='Позначити як успішну')
    def mark_success(self, request, queryset):
        updated = 0
        for p in queryset.select_related('user'):
            if p.status != CertificatePayment.STATUS_SUCCESS:
                p.status = CertificatePayment.STATUS_SUCCESS
                p.paid_at = timezone.now()
                p.save(update_fields=['status', 'paid_at'])
            updated += 1
        self.message_user(request, f'Оновлено: {updated}')


@admin.register(CertificateProgram)
class CertificateProgramAdmin(admin.ModelAdmin):
    list_display = ('slug', 'title', 'level', 'required_lessons_percent', 'required_quiz_percent', 'created_at')
    search_fields = ('slug', 'title')


@admin.register(CertificateEnrollment)
class CertificateEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'program', 'status', 'enrolled_at', 'completed_at')
    list_filter = ('status', 'program', 'enrolled_at')
    search_fields = ('user__username', 'program__slug')


@admin.register(CertificateIssue)
class CertificateIssueAdmin(admin.ModelAdmin):
    list_display = ('certificate_id', 'full_name', 'enrollment', 'issued_at')
    search_fields = ('certificate_id', 'full_name', 'enrollment__user__username')


@admin.register(CertificateProgramLesson)
class CertificateProgramLessonAdmin(admin.ModelAdmin):
    list_display = ('program', 'order', 'lesson')
    list_filter = ('program',)
    search_fields = ('program__slug', 'lesson__title')
