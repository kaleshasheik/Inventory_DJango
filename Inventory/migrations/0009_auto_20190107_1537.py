# Generated by Django 2.1.4 on 2019-01-07 10:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Inventory', '0008_auto_20190104_2156'),
    ]

    operations = [
        migrations.AddField(
            model_name='requestinventory',
            name='datacardNO',
            field=models.CharField(max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='requestinventory',
            name='laptopNO',
            field=models.CharField(max_length=30, null=True),
        ),
    ]
