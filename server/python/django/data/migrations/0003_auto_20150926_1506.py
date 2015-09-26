# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0002_auto_20150926_1459'),
    ]

    operations = [
        migrations.AlterField(
            model_name='position',
            name='time',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
