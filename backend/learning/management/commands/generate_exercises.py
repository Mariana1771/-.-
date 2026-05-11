import random
import re

from django.core.management.base import BaseCommand
from django.db import transaction

from learning.models import Exercise, Lesson


def _strip_html(html: str) -> str:
    s = html or ""
    s = s.replace("<br/>", "\n").replace("<br />", "\n").replace("<br>", "\n")
    s = s.replace("</tr>", "\n").replace("</td>", " ").replace("</p>", "\n")
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("\xa0", " ")
    s = s.replace("Slovíčka z textu:", "\nSlovíčka z textu:\n")
    s = re.sub(r"[ \t]+", " ", s)
    # split sentences that got glued together
    s = re.sub(r"([.!?])([A-ZÁÄČĎÉÍĽŇÓÔŔŠŤÚÝŽ])", r"\1\n\2", s)
    s = re.sub(r"\n{2,}", "\n", s)
    return s.strip()


def _extract_pairs(text: str):
    """
    Extract (left,right) pairs from plain text.
    Supports:
      - 'slovak — ukr'
      - 'slovak - ukr' (like '0 - nula')
    """
    pairs: list[tuple[str, str]] = []

    def add_pair(left: str, right: str):
        left = (left or "").strip(" :;•-–\t")
        right = (right or "").strip(" :;•-–\t")
        if 1 <= len(left) <= 90 and 1 <= len(right) <= 140:
            pairs.append((left, right))

    cyr_re = re.compile(r"[А-Яа-яІіЇїЄєҐґ]")

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue

        # 0) handle "0 - nula 1 - jeden ..." in a single line (tables)
        num_matches = list(
            re.finditer(
                r"(?P<num>\d{1,3})\s*-\s*(?P<word>[A-Za-zÁÄČĎÉÍĹĽŇÓÔŔŠŤÚÝŽáäčďéíĺľňóôŕšťúýž]+)",
                line,
            )
        )
        if num_matches:
            for m in num_matches:
                add_pair(m.group("num"), m.group("word"))
            # Do not parse the rest of this line (prevents "17 — sedemnásť 18 — osemnásť" as one pair)
            continue

        # remove leading emoji-like tokens
        line = re.sub(r"^[^\wА-Яа-яІіЇїЄєҐґ]+", "", line).strip()
        if not line:
            continue

        # 1) pattern: Slovak — Ukrainian (or with hyphen)
        norm = (
            line.replace(" – ", " — ")
            .replace(" - ", " — ")
            .replace("—", " — ")
            .replace("–", " — ")
        )
        if " — " in norm:
            left, right = norm.split(" — ", 1)
            add_pair(left, right)
            continue

        # 2) pattern: Slovak (Українська)   e.g. "Pošta (Пошта)" or with trailing punctuation ") ."
        m = re.match(r"^(.*?)\s*\((.*?)\)\s*[.!?…]*\s*$", line)
        if m:
            left, right = m.group(1).strip(), m.group(2).strip()
            if cyr_re.search(right):
                add_pair(left, right)
                continue

        # 3) pattern: Word: переклад (for connector lists)
        m2 = re.match(r"^([^:]{1,40}):\s*(.+)$", line)
        if m2 and cyr_re.search(m2.group(2)):
            left = m2.group(1).strip()
            right = m2.group(2).strip()
            # keep only short "connector" style left parts (no long sentences)
            if len(left.split()) <= 3 and len(right) <= 80:
                add_pair(left, right)
                continue

        # 4) pattern: X -> Y (examples)
        m3 = re.match(r"^(.+?)\s*->\s*(.+)$", line)
        if m3:
            left, right = m3.group(1).strip(), m3.group(2).strip()
            if left and right:
                add_pair(left, right)
            continue

        # 5) passive table style: "-ný Kúpiť, Pozvať Kúpený, Pozvaný"
        m4 = re.match(r"^-\w+\s+(.+?)\s+([A-Za-zÁÄČĎÉÍĹĽŇÓÔŔŠŤÚÝŽáäčďéíĺľňóôŕšťúýž, ]+)$", line)
        if m4:
            verbs = [v.strip() for v in m4.group(1).split(",") if v.strip()]
            forms = [v.strip() for v in m4.group(2).split(",") if v.strip()]
            if verbs and forms and len(verbs) == len(forms):
                for v, f in zip(verbs, forms):
                    add_pair(v, f)
            continue

    # de-dupe
    uniq = []
    seen = set()
    for a, b in pairs:
        k = (a.lower(), b.lower())
        if k in seen:
            continue
        seen.add(k)
        uniq.append((a, b))
    return uniq


def _pick_distractors(correct: str, pool: list[str], k: int = 2) -> list[str]:
    pool = [p for p in pool if p and p.lower() != correct.lower()]
    random.shuffle(pool)
    out = []
    for p in pool:
        if p.lower() in {x.lower() for x in out}:
            continue
        out.append(p)
        if len(out) >= k:
            break
    while len(out) < k:
        out.append("—")
    return out


class Command(BaseCommand):
    help = "Generate multiple-choice exercises for all lessons (tops up to target per lesson)."

    def add_arguments(self, parser):
        parser.add_argument("--target", type=int, default=12, help="Desired exercises per lesson (max 15 recommended).")
        parser.add_argument("--max", type=int, default=15, help="Hard cap per lesson.")
        parser.add_argument("--dry-run", action="store_true", help="Print what would be created, without DB writes.")

    @transaction.atomic
    def handle(self, *args, **opts):
        target = max(1, min(int(opts["target"]), int(opts["max"])))
        max_per = max(1, int(opts["max"]))
        dry = bool(opts["dry_run"])

        lessons = Lesson.objects.all().order_by("level", "order", "id")
        total_created = 0

        for lesson in lessons:
            existing = Exercise.objects.filter(lesson=lesson).count()
            if existing >= target:
                continue

            text = _strip_html(lesson.theory)
            pairs = _extract_pairs(text)

            # pools for distractors
            left_pool = [a for a, _ in pairs]
            right_pool = [b for _, b in pairs]

            to_create = min(target - existing, max_per - existing)
            if to_create <= 0:
                continue

            candidates = []
            # Prefer translation tasks if we have pairs
            if pairs:
                random.shuffle(pairs)
                for (a, b) in pairs:
                    # Special handling for numbers: clearer questions
                    if a.isdigit() and re.match(r"^[A-Za-zÁÄČĎÉÍĹĽŇÓÔŔŠŤÚÝŽáäčďéíĺľňóôŕšťúýž]+$", b):
                        candidates.append((f"Як словацькою число {a}?", b, right_pool))
                        candidates.append((f"Яке число означає «{b}»?", a, left_pool))
                    else:
                        candidates.append(("Переклад: " + a, b, right_pool))
                        candidates.append(("Як словацькою: " + b, a, left_pool))

            # If no pairs found, fallback to simple fact questions from title
            if not candidates:
                candidates = [
                    (f"Це урок про: {lesson.title}. Оберіть варіант «OK».", "OK", ["OK", "—", "—"])
                ]

            created_here = 0
            used_questions = set(
                q.lower() for q in Exercise.objects.filter(lesson=lesson).values_list("question", flat=True)
            )

            for (q, correct, pool) in candidates:
                if created_here >= to_create:
                    break
                if q.lower() in used_questions:
                    continue
                used_questions.add(q.lower())

                d1, d2 = _pick_distractors(correct, pool, k=2)
                options = [correct, d1, d2]
                random.shuffle(options)

                if dry:
                    self.stdout.write(f"[dry] lesson {lesson.id} create: {q} -> {correct} opts={options}")
                else:
                    Exercise.objects.create(
                        lesson=lesson,
                        question=q,
                        exercise_type=Exercise.TYPE_CHOICE,
                        correct_answer=correct,
                        option_a=options[0],
                        option_b=options[1],
                        option_c=options[2],
                        order=1000 + existing + created_here + 1,
                    )
                created_here += 1

            total_created += created_here
            self.stdout.write(f"Lesson {lesson.id} ({lesson.title}): {existing} -> {existing + created_here}")

        if dry:
            self.stdout.write(self.style.WARNING("Dry run: no changes written."))
        self.stdout.write(self.style.SUCCESS(f"Done. Created {total_created} exercises."))

