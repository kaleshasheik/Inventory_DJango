# Generated by Django 2.1.4 on 2019-01-07 12:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Inventory', '0012_auto_20190107_1717'),
    ]

    operations = [
        migrations.AddField(
            model_name='requestinventory',
            name='Request_id',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
