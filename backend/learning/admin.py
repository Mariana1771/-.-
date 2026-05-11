from django.contrib import admin
from django.utils import timezone
from .models import Lesson, Exercise, QuizQuestion, LessonProgress, QuizAttempt, UserProfile, PremiumPayment, PersonalWord


class ExerciseInline(admin.TabularInline):
    model = Exercise
    extra = 1
    fields = ('question', 'exercise_type', 'correct_answer', 'option_a', 'option_b', 'option_c', 'order')


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'level', 'icon', 'order')
    list_filter = ('level',)
    ordering = ('order',)
    inlines = [ExerciseInline]


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ('question', 'level', 'correct_index')
    list_filter = ('level',)


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'completed', 'xp_earned', 'completed_at')
    list_filter = ('completed',)


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'score', 'total', 'xp_earned', 'taken_at')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_xp', 'is_premium', 'level_name')
    list_filter = ('is_premium',)


@admin.register(PremiumPayment)
class PremiumPaymentAdmin(admin.ModelAdmin):
    actions = ('mark_success_and_activate',)
    list_display = ('user', 'amount_uah', 'period_months', 'status', 'reference', 'transaction_id', 'created_at', 'paid_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'transaction_id', 'reference')

    @admin.action(description='Позначити як успішну та активувати Premium')
    def mark_success_and_activate(self, request, queryset):
        updated = 0
        for p in queryset.select_related('user'):
            if p.status != PremiumPayment.STATUS_SUCCESS:
                p.status = PremiumPayment.STATUS_SUCCESS
                p.paid_at = timezone.now()
                p.save(update_fields=['status', 'paid_at'])
            profile, _ = UserProfile.objects.get_or_create(user=p.user)
            if not profile.is_premium:
                profile.is_premium = True
                profile.save(update_fields=['is_premium'])
            updated += 1
        self.message_user(request, f'Оновлено: {updated}')


@admin.register(PersonalWord)
class PersonalWordAdmin(admin.ModelAdmin):
    list_display = ('user', 'source_word', 'translated_word', 'created_at')
    search_fields = ('user__username', 'source_word', 'translated_word')

from .models import PlacementQuestion

@admin.register(PlacementQuestion)
class PlacementQuestionAdmin(admin.ModelAdmin):
    list_display = ('question', 'level', 'correct_index', 'order')
    list_filter = ('level',)
    ordering = ('level', 'order')
