# Generated by Django 3.1.4 on 2022-03-16 14:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('locomotives', '0015_auto_20220304_1334'),
    ]

    operations = [
        migrations.AlterField(
            model_name='route',
            name='name',
            field=models.CharField(max_length=1000),
        ),
    ]
