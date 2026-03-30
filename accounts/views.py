from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from learning.models import UserProfile, LessonProgress, QuizAttempt, Lesson

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

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
            
            login(request, user)
            messages.success(request, f'Ласкаво просимо, {name}! 🌸')
            return redirect('dashboard')

    # Передаємо request.POST як 'form', щоб зберегти введені дані в полях при помилці
    return render(request, 'accounts/register.html', {
        'errors': errors, 
        'form': request.POST if request.method == 'POST' else None
    })

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect(request.GET.get('next', 'dashboard'))
        
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
        messages.success(request, 'Фото профілю оновлено! ✨')
        return redirect('profile')

    # Статистика для профілю
    completed = LessonProgress.objects.filter(user=request.user, completed=True).count()
    total_lessons = Lesson.objects.count()
    quiz_count = QuizAttempt.objects.filter(user=request.user).count()
    
    return render(request, 'accounts/profile.html', {
        'profile': profile,
        'completed': completed,
        'total_lessons': total_lessons,
        'quiz_count': quiz_count,
    })