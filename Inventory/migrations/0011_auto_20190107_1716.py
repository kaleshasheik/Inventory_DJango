# Generated by Django 2.1.4 on 2019-01-07 11:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Inventory', '0010_auto_20190107_1714'),
    ]

    operations = [
        migrations.AlterField(
            model_name='requestinventory',
            name='id',
            field=models.AutoField(default=1, max_length=100, primary_key=True, serialize=False),
        ),
    ]
