from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0004_premiumpayment'),
    ]

    operations = [
        migrations.CreateModel(
            name='PersonalWord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_word', models.CharField(max_length=100, verbose_name='Слово')),
                ('translated_word', models.CharField(max_length=150, verbose_name='Переклад')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='personal_words', to='auth.user')),
            ],
            options={
                'verbose_name': 'Слово користувача',
                'verbose_name_plural': 'Слова користувачів',
                'ordering': ['-created_at'],
                'unique_together': {('user', 'source_word')},
            },
        ),
    ]
