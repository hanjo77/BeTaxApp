# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0003_auto_20150926_1506'),
    ]

    operations = [
        migrations.AlterField(
            model_name='position',
            name='time',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
