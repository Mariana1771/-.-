from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from learning import views as lv

urlpatterns = [
    # Адмін-панель
    path('admin/', admin.site.urls),
    
    # Головна та Дашборд
    path('', lv.home, name='home'),
    path('dashboard/', lv.dashboard, name='dashboard'),
    
    # Акаунти (Логін, Реєстрація, Вихід)
    path('accounts/', include('accounts.urls')),
    
    # Навчання: Граматика та Вправи
    path('grammar/', lv.grammar_list, name='grammar_list'),
    path('grammar/<int:lesson_id>/', lv.lesson_detail, name='lesson_detail'),
    path('grammar/<int:lesson_id>/exercise/', lv.exercise, name='exercise'),
    
    # Тести (Quiz)
    path('quiz/', lv.quiz, name='quiz'),
    path('quiz/result/', lv.quiz_result, name='quiz_result'),
    
    # Додаткові розділи
    path('stats/', lv.stats, name='stats'),
    path('dictionary/', lv.dictionary, name='dictionary'),
    path('texts/', lv.texts, name='texts'),
]

# Цей блок дозволяє Django "бачити" завантажені фото профілю під час розробки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)