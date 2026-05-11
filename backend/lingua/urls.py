from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from learning import views as lv

urlpatterns = [
    # REST API для SPA (`frontend/`), префікс не перетинається з `/api/add-word/` тощо.
    path('api/v1/', include('api.urls')),
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
    path('placement/', lv.placement_test, name='placement_test'),
    path('placement/result/', lv.placement_result, name='placement_result'),
    path('my-words/', lv.my_words, name='my_words'),
    path('api/add-word/', lv.add_word, name='add_word'),
    path('api/toggle-learned/<int:word_id>/', lv.toggle_learned, name='toggle_learned'),
    path('api/delete-word/<int:word_id>/', lv.delete_word, name='delete_word'),
    path('texts/<int:lesson_id>/', lv.text_reader, name='text_reader'),
    re_path(r'^texts/(?P<lesson_id>\d+)/$', lv.text_reader, name='text_reader_fallback'),
    path('api/translate-word/', lv.translate_word, name='translate_word'),
    path('api/add-personal-word/', lv.add_personal_word, name='add_personal_word'),
]

# Цей блок дозволяє Django "бачити" завантажені фото профілю під час розробки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
