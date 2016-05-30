# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-30 10:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('runstat', '0003_remove_postattachments_title'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='groupmember',
            name='administrator',
        ),
        migrations.AddField(
            model_name='groupmember',
            name='age',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='age of a member'),
        ),
        migrations.AddField(
            model_name='groupmember',
            name='sex',
            field=models.CharField(blank=True, choices=[('m', 'male'), ('f', 'female')], default=None, max_length=1, null=True, verbose_name='sex of a member'),
        ),
    ]
