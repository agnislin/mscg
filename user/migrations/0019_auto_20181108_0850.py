# Generated by Django 2.1.3 on 2018-11-08 08:50

from django.db import migrations, models
import django.db.models.deletion
import user.models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0018_auto_20181020_1418'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='notice',
            name='receiver',
        ),
        migrations.AddField(
            model_name='notice',
            name='receiver',
            field=models.ManyToManyField(to='user.Role'),
        ),
        migrations.AlterField(
            model_name='staff',
            name='photo',
            field=models.ImageField(default='default/default.jpg', upload_to=user.models.user_photo_path),
        ),
        migrations.AlterField(
            model_name='staff',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='user.User'),
        ),
    ]
