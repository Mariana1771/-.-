from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Avg
import random

from .models import Lesson, Exercise, QuizQuestion, LessonProgress, QuizAttempt, UserProfile

def get_or_create_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile

# --------- ГОЛОВНА ТА ДЕШБОРД ---------
def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    features = [
        ('📚', 'Граматика', 'Рівні A1 → B2'),
        ('✏️', 'Вправи', 'Після кожної теми'),
        ('🧠', 'Тести', 'Перевір себе'),
        ('📊', 'Статистика', 'Твій прогрес'),
    ]
    return render(request, 'learning/home.html', {'features': features})

@login_required
def dashboard(request):
    lessons = Lesson.objects.all()
    profile = get_or_create_profile(request.user)
    completed_ids = set(
        LessonProgress.objects.filter(user=request.user, completed=True)
        .values_list('lesson_id', flat=True)
    )
    recent_lessons = lessons.order_by('-id')[:4]
    context = {
        'lessons': recent_lessons,
        'completed_ids': completed_ids,
        'profile': profile,
        'total_lessons': lessons.count(),
    }
    return render(request, 'learning/dashboard.html', context)

# --------- СПИСОК УРОКІВ ТА ДЕТАЛІ ---------
def grammar_list(request):
    if request.user.is_authenticated:
        profile = get_or_create_profile(request.user)
        completed_ids = set(LessonProgress.objects.filter(user=request.user, completed=True).values_list('lesson_id', flat=True))
    else:
        profile, completed_ids = None, set()

    context = {
        'a1_lessons': Lesson.objects.filter(level='A1').exclude(title__icontains='Словник').exclude(title__icontains='Текст').order_by('id'),
        'a2_lessons': Lesson.objects.filter(level='A2').exclude(title__icontains='Словник').exclude(title__icontains='Текст').order_by('id'),
        'b1_lessons': Lesson.objects.filter(level='B1').exclude(title__icontains='Словник').exclude(title__icontains='Текст').order_by('id'),
        'completed_ids': completed_ids,
        'profile': profile,
    }
    return render(request, 'learning/grammar_list.html', context)

def lesson_detail(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    # Отримуємо вправи для цього уроку
    exercises = Exercise.objects.filter(lesson=lesson).order_by('order', 'id')
    return render(request, 'learning/lesson_detail.html', {
        'lesson': lesson,
        'exercises': exercises
    })

# --------- ЛОГІКА ВПРАВ (EXERCISE) ---------
def exercise(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    exercises = list(Exercise.objects.filter(lesson=lesson).order_by('order', 'id'))

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

    if request.method == 'POST':
        user_answer = request.POST.get('answer', '').strip().lower()
        current_ex = exercises[idx]
        correct_answer = str(current_ex.correct_answer).strip().lower()

        # Перевірка відповіді
        if user_answer == correct_answer:
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

            return render(request, 'learning/exercise_done.html', {
                'lesson': lesson, 'score': final_score, 'total': len(exercises), 'xp': xp
            })
        
        return redirect('exercise', lesson_id=lesson_id)

    # Відображення поточної вправи
    ex = exercises[idx]
    return render(request, 'learning/exercise.html', {
        'lesson': lesson,
        'ex': ex,
        'idx': idx,
        'total': len(exercises),
        'options': ex.get_options() if ex.exercise_type == Exercise.TYPE_CHOICE else [],
    })

# --------- ТЕСТИ (QUIZ) ---------
def quiz(request):
    if request.method == 'POST':
        # Отримуємо ID питань, які були в цьому тесті
        question_ids = request.session.get('quiz_question_ids', [])
        questions = QuizQuestion.objects.filter(id__in=question_ids)
        
        # Рахуємо правильні відповіді
        score = 0
        for q in questions:
            user_ans = request.POST.get(f'q_{q.id}')
            if user_ans == str(q.correct_index):
                score += 1
        
        # Створюємо запис про спробу
        attempt = QuizAttempt.objects.create(
            user=request.user if request.user.is_authenticated else None,
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
        
        # Очищаємо список питань з сесії, щоб тест не "зациклився"
        if 'quiz_question_ids' in request.session:
            del request.session['quiz_question_ids']
            
        return redirect('quiz_result')

    # GET запит: підготовка нових питань
    all_q = list(QuizQuestion.objects.all())
    if not all_q:
        messages.warning(request, "У базі ще немає питань для тестів.")
        return redirect('dashboard')
        
    # Вибираємо 6 випадкових питань (або менше, якщо в базі мало)
    questions = random.sample(all_q, min(6, len(all_q)))
    request.session['quiz_question_ids'] = [q.id for q in questions]
    
    return render(request, 'learning/quiz.html', {'questions': questions})

def quiz_result(request):
    # Дістаємо ID останньої спроби
    attempt_id = request.session.get('last_quiz_id')
    
    if not attempt_id:
        # Якщо людина зайшла на сторінку результату просто так - повертаємо на тест
        return redirect('quiz')
        
    attempt = get_object_or_404(QuizAttempt, id=attempt_id)
    
    return render(request, 'learning/quiz_result.html', {
        'attempt': attempt
    })

# --------- СТАТИСТИКА ТА ІНШЕ ---------
@login_required
def stats(request):
    profile = get_or_create_profile(request.user)
    progress_qs = LessonProgress.objects.filter(user=request.user, completed=True)
    quiz_attempts = QuizAttempt.objects.filter(user=request.user)
    avg_quiz = quiz_attempts.aggregate(Avg('score'))['score__avg'] or 0
    
    return render(request, 'learning/stats.html', {
        'profile': profile,
        'progress_list': progress_qs,
        'quiz_attempts': quiz_attempts.order_by('-taken_at')[:10],
        'total_lessons': Lesson.objects.count(),
        'completed_count': progress_qs.count(),
        'avg_quiz_pct': round(avg_quiz / 6 * 100) if quiz_attempts.exists() else 0,
    })

def dictionary(request):
    return render(request, 'learning/dictionary.html', {'lessons': Lesson.objects.filter(title__icontains='Словник')})

def texts(request):
    return render(request, 'learning/texts.html', {'texts': Lesson.objects.filter(title__icontains='Текст')})

def alphabet(request):
    return render(request, 'learning/alphabet.html')