from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.db.models import Prefetch
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
import requests

from learning.models import Exercise, Lesson
from learning.views import has_lesson_access

from .serializers import LessonDetailSerializer, LessonListSerializer, UserMeSerializer


class CsrfCookieView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        token = get_token(request)
        return Response({"csrfToken": token})


class LoginApiView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = (request.data.get("username") or "").strip()
        password = request.data.get("password") or ""
        user = authenticate(request, username=username, password=password)
        if not user:
            return Response({"detail": "Невірний логін або пароль."}, status=status.HTTP_400_BAD_REQUEST)
        login(request, user)
        return Response(UserMeSerializer(user).data)


class LogoutApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CurrentUserApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserMeSerializer(request.user).data)


class LessonListApiView(generics.ListAPIView):
    """
    Спрощений список уроків для SPA (як основний навчальний контур без CERT у фільтрі за замовчуванням).
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = LessonListSerializer

    def get_queryset(self):
        qs = Lesson.objects.all().order_by("level", "order", "id")
        scope = self.request.query_params.get("scope", "main").lower()
        if scope == "main":
            qs = qs.filter(course_tag="")
        return qs


class LessonDetailApiView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = LessonDetailSerializer
    lookup_field = "pk"

    def get_queryset(self):
        return Lesson.objects.prefetch_related(
            Prefetch(
                "exercises",
                queryset=Exercise.objects.order_by("order", "id"),
            )
        )

    def retrieve(self, request, *args, **kwargs):
        lesson = self.get_object()
        if not has_lesson_access(request.user, lesson):
            return Response(
                {"detail": "Немає доступу до цього уроку.", "lesson_id": lesson.id},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = self.get_serializer(lesson)
        return Response(serializer.data)


class TranslateApiView(APIView):
    """
    Переклад тексту з використанням MyMemory API.
    Запит: POST /api/translate/
    Тіло: {"text": "hello", "source_lang": "sk", "target_lang": "uk"}
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        text = (request.data.get("text") or "").strip()
        source_lang = request.data.get("source_lang", "sk")
        target_lang = request.data.get("target_lang", "uk")

        if not text:
            return Response(
                {"detail": "Текст не надано."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # MyMemory API: https://mymemory.translated.net/doc/spec.php
            url = "https://api.mymemory.translated.net/get"
            params = {
                "q": text,
                "langpair": f"{source_lang}|{target_lang}"
            }
            
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            if data.get("responseStatus") == 200:
                translation = data.get("responseData", {}).get("translatedText", text)
                return Response({
                    "text": text,
                    "translation": translation,
                    "source_lang": source_lang,
                    "target_lang": target_lang
                })
            else:
                return Response({
                    "text": text,
                    "translation": text,
                    "source_lang": source_lang,
                    "target_lang": target_lang
                })
        except Exception as e:
            return Response({
                "text": text,
                "translation": text,
                "error": str(e)
            }, status=status.HTTP_200_OK)
