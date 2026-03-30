# LinguaUA — Django + MySQL

Застосунок для вивчення англійської мови.
Граматика по рівнях · Вправи · Тести · Статистика прогресу

---

## Структура проєкту

```
lingua/
├── lingua/                  ← налаштування проєкту
│   ├── settings.py          ← конфіг (БД, apps, templates)
│   ├── urls.py              ← головні маршрути
│   └── wsgi.py
├── accounts/                ← реєстрація, вхід, профіль
│   ├── views.py
│   └── urls.py
├── learning/                ← уроки, вправи, тести, статистика
│   ├── models.py            ← Lesson, Exercise, Quiz, Progress
│   ├── views.py
│   ├── admin.py
│   └── fixtures/
│       └── initial_data.json   ← готові уроки і питання тестів
├── templates/
│   ├── base.html            ← базовий шаблон (рожевий дизайн)
│   ├── accounts/            ← login.html, register.html, profile.html
│   └── learning/            ← dashboard, grammar, lesson, exercise, quiz, stats
├── manage.py
└── requirements.txt
```

---

## Налаштування MySQL

### 1. Створити базу і користувача

```sql
-- Увійди в MySQL як root:
mysql -u root -p

CREATE DATABASE lingua_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'lingua_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON lingua_db.* TO 'lingua_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 2. Оновити пароль у settings.py

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'lingua_db',
        'USER': 'lingua_user',
        'PASSWORD': 'your_password',   # ← змін тут
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

---

## Запуск

```bash
# 1. Встановити залежності
pip install -r requirements.txt

# Якщо mysqlclient не встановлюється:
# Ubuntu/Debian: sudo apt install python3-dev default-libmysqlclient-dev build-essential
# macOS:         brew install mysql-client

# 2. Застосувати міграції
python manage.py migrate

# 3. Завантажити початкові дані (уроки + тести)
python manage.py loaddata learning/fixtures/initial_data.json

# 4. Створити адміністратора
python manage.py createsuperuser

# 5. Запустити
python manage.py runserver
```

Відкрий: http://127.0.0.1:8000
Адмін:   http://127.0.0.1:8000/admin/

---

## Моделі (learning/models.py)

| Модель | Опис |
|--------|------|
| `Lesson` | Урок з теорією, рівнем A1-B2, іконкою |
| `Exercise` | Вправа до уроку: заповни пропуск або вибір |
| `QuizQuestion` | Питання загального тесту |
| `LessonProgress` | Прогрес конкретного користувача по уроку |
| `QuizAttempt` | Результат тесту з XP і датою |
| `UserProfile` | Загальний XP і рівень користувача |

---

## Функціонал

- Реєстрація / вхід / вихід (Django auth)
- Граматика по рівнях A1 - B2
- Вправи після теорії (fill-in + multiple choice)
- Тест із випадковими питаннями
- Статистика: XP, прогрес, результати тестів, рекомендації
- Профіль з рівнем і XP
- Гостьовий режим (без збереження)

---

## Додавання контенту

Через адмін-панель /admin/ без коду:
- Нові уроки і вправи
- Питання для тесту
- Перегляд прогресу учнів
