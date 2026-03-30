from django.contrib import admin
from .models import Lesson, Exercise, QuizQuestion, LessonProgress, QuizAttempt, UserProfile


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
    list_display = ('user', 'total_xp', 'level_name')
