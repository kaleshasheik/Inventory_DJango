# Generated by Django 2.1.4 on 2019-01-04 16:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Inventory', '0005_auto_20190104_2131'),
    ]

    operations = [
        migrations.AddField(
            model_name='requestinventory',
            name='status',
            field=models.CharField(default='Created', max_length=30),
        ),
    ]
