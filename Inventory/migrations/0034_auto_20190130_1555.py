# Generated by Django 2.1.4 on 2019-01-30 10:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Inventory', '0033_auto_20190130_1522'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventoryvalues',
            name='status',
            field=models.CharField(default='Available', max_length=100),
        ),
    ]
