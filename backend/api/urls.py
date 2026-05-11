from django.urls import path

from . import views

urlpatterns = [
    path("csrf/", views.CsrfCookieView.as_view(), name="api_csrf"),
    path("auth/login/", views.LoginApiView.as_view(), name="api_auth_login"),
    path("auth/logout/", views.LogoutApiView.as_view(), name="api_auth_logout"),
    path("auth/me/", views.CurrentUserApiView.as_view(), name="api_auth_me"),
    path("lessons/", views.LessonListApiView.as_view(), name="api_lesson_list"),
    path("lessons/<int:pk>/", views.LessonDetailApiView.as_view(), name="api_lesson_detail"),
    path("translate/", views.TranslateApiView.as_view(), name="api_translate"),
]
