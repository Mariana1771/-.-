from django.db import models
from django.contrib.auth.models import User


LEVEL_CHOICES = [
    ('A1', 'A1 — Початковий'),
    ('A2', 'A2 — Базовий'),
    ('B1', 'B1 — Середній'),
    ('B2', 'B2 — Вище середнього'),
]


class Lesson(models.Model):
    title = models.CharField(max_length=200, verbose_name='Назва')
    level = models.CharField(max_length=2, choices=LEVEL_CHOICES, verbose_name='Рівень')
    icon = models.CharField(max_length=10, default='📖', verbose_name='Іконка')
    theory = models.TextField(verbose_name='Теорія (HTML)')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        ordering = ['order']
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'

    def __str__(self):
        return f'[{self.level}] {self.title}'

    @property
    def xp_reward(self):
        return self.exercises.count() * 10


class Exercise(models.Model):
    TYPE_FILL = 'fill'
    TYPE_CHOICE = 'choice'
    TYPE_CHOICES = [
        (TYPE_FILL, 'Заповни пропуск'),
        (TYPE_CHOICE, 'Вибір варіанту'),
    ]

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='exercises')
    question = models.CharField(max_length=500, verbose_name='Запитання')
    exercise_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=TYPE_FILL)
    correct_answer = models.CharField(max_length=200, verbose_name='Правильна відповідь')
    option_a = models.CharField(max_length=200, blank=True)
    option_b = models.CharField(max_length=200, blank=True)
    option_c = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Вправа'
        verbose_name_plural = 'Вправи'

    def __str__(self):
        return f'{self.lesson.title} — {self.question[:50]}'

    def get_options(self):
        return [o for o in [self.option_a, self.option_b, self.option_c] if o]


class QuizQuestion(models.Model):
    level = models.CharField(max_length=2, choices=LEVEL_CHOICES)
    question = models.CharField(max_length=500)
    option_a = models.CharField(max_length=200)
    option_b = models.CharField(max_length=200)
    option_c = models.CharField(max_length=200)
    correct_index = models.PositiveSmallIntegerField(help_text='0=A, 1=B, 2=C')

    class Meta:
        verbose_name = 'Питання тесту'
        verbose_name_plural = 'Питання тестів'

    def __str__(self):
        return f'[{self.level}] {self.question[:60]}'

    def get_options(self):
        return [self.option_a, self.option_b, self.option_c]


class LessonProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    xp_earned = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'lesson')
        verbose_name = 'Прогрес уроку'

    def __str__(self):
        return f'{self.user.username} — {self.lesson.title}'


class QuizAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts', null=True, blank=True)
    score = models.PositiveSmallIntegerField()
    total = models.PositiveSmallIntegerField()
    xp_earned = models.PositiveIntegerField(default=0)
    taken_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-taken_at']
        verbose_name = 'Спроба тесту'

    def __str__(self):
        return f'{self.user} — {self.score}/{self.total}'

    @property
    def percent(self):
        return round(self.score / self.total * 100) if self.total else 0


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    total_xp = models.PositiveIntegerField(default=0)
    avatar = models.ImageField(
        upload_to='avatars/', 
        null=True, 
        blank=True, 
        verbose_name='Фото профілю'
    )

    def __str__(self):
        return f'Profile: {self.user.username}'

    @property
    def level_name(self):
        if self.total_xp < 100: return 'Початківець'
        elif self.total_xp < 300: return 'Базовий'
        elif self.total_xp < 600: return 'Середній'
        return 'Просунутий'
