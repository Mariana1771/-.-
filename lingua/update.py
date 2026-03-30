import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lingua.settings')

import django
django.setup()

from learning.models import Lesson

# Оновити урок 1 — прибрати алфавіт
l = Lesson.objects.get(id=1)
l.theory = """<div class="theory-block"><h3><span class="section-icon">💬</span>Загальні фрази</h3><table class="phrases-table"><tr><td>Dobré ráno</td><td>Добрий ранок</td></tr><tr><td>Dobrý deň</td><td>Доброго дня</td></tr><tr><td>Dobrý večer</td><td>Добрий вечір</td></tr><tr><td>Dobrú noc</td><td>На добраніч</td></tr><tr><td>Ahoj / Čau</td><td>Привіт / Бувай</td></tr><tr><td>Dovidenia</td><td>До побачення</td></tr><tr><td>Ďakujem pekne</td><td>Дуже дякую</td></tr><tr><td>Nie je za čo</td><td>Нема за що</td></tr><tr><td>Prepáčte</td><td>Вибачте</td></tr><tr><td>Nech sa páči</td><td>Будь ласка</td></tr><tr><td>Áno / Nie</td><td>Так / Ні</td></tr></table></div><div class="theory-block" style="margin-bottom:0;"><h3><span class="section-icon">🤝</span>Знайомство</h3><table class="phrases-table"><tr><td>Ako sa voláš?</td><td>Як тебе звати?</td></tr><tr><td>Volám sa...</td><td>Мене звати...</td></tr><tr><td>Teší ma</td><td>Дуже приємно</td></tr><tr><td>Odkiaľ si?</td><td>Звідки ти?</td></tr><tr><td>Som z Ukrajiny</td><td>Я з України</td></tr><tr><td>Ako sa máš?</td><td>Як у тебе справи?</td></tr><tr><td>Mám sa dobre</td><td>У мене все добре</td></tr><tr><td>V pohode</td><td>Нормально</td></tr></table></div>"""
l.save()
print("Урок 1 оновлено!")

# Створити новий урок Алфавіт
new = Lesson(title='Алфавіт — Abeceda', level='A1', icon='', theory='', order=0)
new.save()
print("Новий урок id:", new.id)