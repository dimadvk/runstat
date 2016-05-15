# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-15 13:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='GroupMember',
            fields=[
                ('object_id', models.BigIntegerField(primary_key=True, serialize=False, unique=True, verbose_name='member object id')),
                ('name', models.CharField(max_length=256, verbose_name='member name')),
                ('administrator', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='GroupPost',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.CharField(max_length=100, unique=True, verbose_name='post object id')),
                ('author', models.BigIntegerField(verbose_name='author object id')),
                ('message', models.TextField(blank=True, null=True, verbose_name='post message')),
                ('created_time', models.DateTimeField(verbose_name='post created time')),
                ('updated_time', models.DateTimeField(null=True, verbose_name='post updated time')),
            ],
        ),
        migrations.CreateModel(
            name='PostAttachments',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('post', models.CharField(max_length=100, unique=True, verbose_name='post object id')),
                ('url', models.URLField(default='', max_length=1000)),
                ('url_x600', models.URLField(default='', max_length=1000)),
                ('url_x480', models.URLField(default='', max_length=1000)),
                ('title', models.CharField(blank=True, default='', max_length=255)),
            ],
        ),
    ]
