# Generated by Django 2.1.4 on 2019-01-21 09:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Inventory', '0022_remove_customuser_designation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='requestinventory',
            name='status',
            field=models.CharField(default='Pending With L1', max_length=30),
        ),
    ]