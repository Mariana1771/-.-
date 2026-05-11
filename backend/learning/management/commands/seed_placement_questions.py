from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed basic PlacementQuestion rows (A1–B2) if table is empty."

    def handle(self, *args, **options):
        from learning.models import PlacementQuestion

        if PlacementQuestion.objects.exists():
            self.stdout.write(self.style.SUCCESS("PlacementQuestion already has data. Skipping."))
            return

        seed = [
            # A1
            ("A1", "Ako sa voláš?", "Volám sa Anna.", "Mám 20 rokov.", "Bývam doma.", 0),
            ("A1", "Doplň: Ja ___ študent.", "som", "si", "je", 0),
            ("A1", "Doplň: Ty ___ z Ukrajiny.", "som", "si", "je", 1),
            ("A1", "Vyber správne: Mám ___ knihu.", "jeden", "jednu", "jedno", 1),
            ("A1", "Čo je to? (stôl)", "table", "chair", "door", 0),
            # A2
            ("A2", "Doplň: Včera som ___ do práce.", "idem", "išiel", "pôjdem", 1),
            ("A2", "Vyber správne: Zajtra ___ na výlet.", "pôjdem", "išiel", "chodím", 0),
            ("A2", "Doplň: Nemám čas, ___ sa učím.", "pretože", "ale", "takže", 0),
            ("A2", "Ktorá veta je správna?", "Vždy pijem kávy.", "Vždy pijem kávu.", "Vždy pijem káva.", 1),
            ("A2", "Doplň: Páči sa mi ___ film.", "tento", "táto", "tieto", 0),
            # B1
            ("B1", "Vyber správne: Keby som mal viac času, ___ by som viac.", "učím sa", "učil by som sa", "učil som sa", 1),
            (
                "B1",
                "Ktorá veta je najprirodzenejšia?",
                "Včera som sa stretol s kamarátom.",
                "Včera som sa stretnúť s kamarátom.",
                "Včera som sa stretol kamarát.",
                0,
            ),
            ("B1", "Doplň: Myslím si, že to ___ dobrý nápad.", "je", "bol", "budem", 0),
            ("B1", "Vyber synonymum k 'dôležitý'", "lacný", "podstatný", "špinavý", 1),
            ("B1", "Doplň: Už som to urobil, ___ sa neboj.", "tak", "preto", "aby", 0),
            # B2
            ("B2", "Vyber správne: Aj keď som bol unavený, ___ som pracoval ďalej.", "predsa", "nikdy", "len", 0),
            (
                "B2",
                "Ktorá veta je správna?",
                "Napriek tomu, že pršalo, išli sme von.",
                "Napriek tomu pršalo, išli sme von.",
                "Napriek že pršalo, išli sme von.",
                0,
            ),
            ("B2", "Vyber význam: 'zvážiť'", "zabudnúť", "premyslieť", "zjesť", 1),
            (
                "B2",
                "Vyber správne: Ak by si mi to povedal skôr, ___ by sme to vyriešili.",
                "mohli",
                "môžeme",
                "mohli sme",
                2,
            ),
            ("B2", "Doplň: Je to otázka, ___ sa nedá odpovedať jednoducho.", "na ktorú", "ktorý", "kto", 0),
        ]

        objs = []
        order = 1
        for level, question, a, b, c, correct_index in seed:
            objs.append(
                PlacementQuestion(
                    level=level,
                    question=question,
                    option_a=a,
                    option_b=b,
                    option_c=c,
                    correct_index=int(correct_index),
                    order=order,
                )
            )
            order += 1

        PlacementQuestion.objects.bulk_create(objs)
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(objs)} placement questions."))

