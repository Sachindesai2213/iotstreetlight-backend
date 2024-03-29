# Generated by Django 4.1.1 on 2023-01-30 11:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='devicedata',
            name='inserted_on',
        ),
        migrations.CreateModel(
            name='DeviceDataLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('inserted_on', models.DateTimeField(auto_now_add=True)),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.device')),
            ],
        ),
        migrations.AddField(
            model_name='devicedata',
            name='log',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='api.devicedatalog'),
        ),
    ]
