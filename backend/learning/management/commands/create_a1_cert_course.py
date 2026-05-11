from django.core.management.base import BaseCommand
from django.db import transaction

from learning.models import Lesson, Exercise
from accounts.models import CertificateProgram, CertificateProgramLesson


class Command(BaseCommand):
    help = "Clone base lessons+exercises into separate *_CERT course for certification programs."

    def add_arguments(self, parser):
        parser.add_argument("--level", default="A1", help="A1/A2/B1/B2")
        parser.add_argument("--tag", default="", help="Override course_tag (default: <LEVEL>_CERT)")
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **opts):
        level = (opts.get("level") or "A1").strip().upper()
        if level not in ("A1", "A2", "B1", "B2"):
            self.stdout.write(self.style.ERROR("Invalid --level. Use A1/A2/B1/B2."))
            return
        tag = (opts.get("tag") or f"{level}_CERT").strip()
        dry = bool(opts.get("dry_run"))

        program, _ = CertificateProgram.objects.get_or_create(
            slug=level.lower(),
            defaults={
                "title": f"{level} Slovak Program",
                "level": level,
                "short_pitch": f"Пройди окремий курс {level}, склади фінальний тест і отримай сертифікат.",
                "required_lessons_percent": 80,
                "required_quiz_percent": 70,
            },
        )

        source_lessons = list(
            Lesson.objects.filter(level=level, course_tag="")
            .exclude(title__icontains="Словник")
            .exclude(title__icontains="Текст")
            .order_by("order", "id")
        )

        if not source_lessons:
            self.stdout.write(self.style.WARNING(f"No source {level} lessons found."))
            return

        self.stdout.write(f"Source lessons ({level}): {len(source_lessons)}")

        # prevent duplicates: if already created, do nothing
        existing_cert = Lesson.objects.filter(level=level, course_tag=tag).count()
        if existing_cert:
            self.stdout.write(self.style.WARNING(f"Lessons with tag={tag} already exist: {existing_cert}. Skip cloning."))
            return

        if dry:
            self.stdout.write(self.style.WARNING("DRY RUN: no changes will be saved."))

        cert_lessons = []
        for src in source_lessons:
            cert_lessons.append(
                Lesson(
                    title=f"{level} Сертифікація: {src.title}",
                    level=level,
                    course_tag=tag,
                    icon=src.icon,
                    theory=src.theory,
                    order=src.order,
                )
            )

        if not dry:
            Lesson.objects.bulk_create(cert_lessons)

        created_lessons = len(cert_lessons)
        created_exercises = 0

        if not dry:
            new_lessons = list(Lesson.objects.filter(level=level, course_tag=tag).order_by("order", "id"))
            for src, dst in zip(source_lessons, new_lessons):
                ex_list = list(Exercise.objects.filter(lesson=src).order_by("order", "id"))
                bulk_ex = []
                for ex in ex_list:
                    bulk_ex.append(
                        Exercise(
                            lesson=dst,
                            question=ex.question,
                            exercise_type=ex.exercise_type,
                            correct_answer=ex.correct_answer,
                            option_a=ex.option_a,
                            option_b=ex.option_b,
                            option_c=ex.option_c,
                            order=ex.order,
                        )
                    )
                if bulk_ex:
                    Exercise.objects.bulk_create(bulk_ex)
                    created_exercises += len(bulk_ex)

            CertificateProgramLesson.objects.filter(program=program).delete()
            bulk_pl = []
            for i, lesson in enumerate(Lesson.objects.filter(level=level, course_tag=tag).order_by("order", "id"), start=1):
                bulk_pl.append(CertificateProgramLesson(program=program, lesson=lesson, order=i))
            if bulk_pl:
                CertificateProgramLesson.objects.bulk_create(bulk_pl)

        self.stdout.write(self.style.SUCCESS(f"Created lessons: {created_lessons}"))
        self.stdout.write(self.style.SUCCESS(f"Created exercises: {created_exercises}"))

