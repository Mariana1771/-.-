from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0002_userprofile_avatar'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='is_premium',
            field=models.BooleanField(default=False, verbose_name='Преміум'),
        ),
    ]
