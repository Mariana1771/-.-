from django.contrib.auth.models import User
from rest_framework import serializers

from learning.models import Exercise, Lesson
from learning.views import get_or_create_profile


class UserMeSerializer(serializers.ModelSerializer):
    is_premium = serializers.SerializerMethodField()
    total_xp = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "is_premium", "total_xp"]

    def get_is_premium(self, obj: User):
        profile = getattr(obj, "profile", None)
        if profile is None:
            profile = get_or_create_profile(obj)
        return profile.is_premium

    def get_total_xp(self, obj: User):
        profile = getattr(obj, "profile", None)
        if profile is None:
            profile = get_or_create_profile(obj)
        return profile.total_xp


class PublicExerciseSerializer(serializers.ModelSerializer):
    """Для SPA: без correct_answer."""

    class Meta:
        model = Exercise
        fields = ["id", "question", "exercise_type", "option_a", "option_b", "option_c", "order"]


class LessonListSerializer(serializers.ModelSerializer):
    xp_reward = serializers.IntegerField(read_only=True)

    class Meta:
        model = Lesson
        fields = [
            "id",
            "title",
            "level",
            "course_tag",
            "icon",
            "order",
            "xp_reward",
        ]


class LessonDetailSerializer(serializers.ModelSerializer):
    xp_reward = serializers.IntegerField(read_only=True)
    exercises = PublicExerciseSerializer(many=True, read_only=True)

    class Meta:
        model = Lesson
        fields = [
            "id",
            "title",
            "level",
            "course_tag",
            "icon",
            "order",
            "xp_reward",
            "theory",
            "exercises",
        ]
