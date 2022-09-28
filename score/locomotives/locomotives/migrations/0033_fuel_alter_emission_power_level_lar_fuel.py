# Generated by Django 4.0.4 on 2022-07-19 13:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('locomotives', '0032_emission_delete_emissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='Fuel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=40)),
            ],
        ),
        migrations.AlterField(
            model_name='emission',
            name='power_level',
            field=models.CharField(choices=[('N2', 'notch 2'), ('N7', 'notch 7'), ('N5', 'notch 5'), ('N3', 'notch 3'), ('N6', 'notch 6'), ('N8', 'notch 8'), ('LI', 'idle'), ('N1', 'notch 1'), ('N4', 'notch 4'), ('DB', 'dynamic brake')], max_length=20),
        ),
        migrations.AddField(
            model_name='lar',
            name='fuel',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='locomotives.fuel'),
        ),
    ]
