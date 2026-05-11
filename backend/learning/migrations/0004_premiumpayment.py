from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0003_userprofile_is_premium'),
    ]

    operations = [
        migrations.CreateModel(
            name='PremiumPayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount_uah', models.PositiveIntegerField(default=199, verbose_name='Сума (грн)')),
                ('status', models.CharField(choices=[('pending', 'Очікує'), ('success', 'Успішно'), ('failed', 'Помилка')], default='pending', max_length=10)),
                ('transaction_id', models.CharField(max_length=40, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('paid_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='premium_payments', to='auth.user')),
            ],
            options={
                'verbose_name': 'Оплата Premium',
                'verbose_name_plural': 'Оплати Premium',
                'ordering': ['-created_at'],
            },
        ),
    ]
