# Generated by Django 2.1.4 on 2019-01-07 15:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Inventory', '0018_auto_20190107_2043'),
    ]

    operations = [
        migrations.AlterField(
            model_name='requestinventory',
            name='status',
            field=models.CharField(default='Pending with L1', max_length=30),
        ),
    ]
