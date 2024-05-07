# Generated by Django 4.1.1 on 2023-10-24 13:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('locomotives', '0035_alter_emission_power_level_yard'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emission',
            name='power_level',
            field=models.CharField(choices=[('LI', 'idle'), ('N3', 'notch 3'), ('N7', 'notch 7'), ('N1', 'notch 1'), ('DB', 'dynamic brake'), ('N4', 'notch 4'), ('N5', 'notch 5'), ('N2', 'notch 2'), ('N6', 'notch 6'), ('N8', 'notch 8')], max_length=20),
        ),
        migrations.AlterField(
            model_name='yard',
            name='origin',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='locomotives.line'),
        ),
    ]
