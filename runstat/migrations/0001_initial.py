# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-24 07:08
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='GroupMember',
            fields=[
                ('object_id', models.BigIntegerField(primary_key=True, serialize=False, unique=True, verbose_name='member object id')),
                ('name', models.CharField(max_length=255, verbose_name='member name')),
                ('administrator', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='GroupPost',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.CharField(max_length=100, unique=True, verbose_name='post object id')),
                ('message', models.TextField(blank=True, null=True, verbose_name='post message')),
                ('created_time', models.DateTimeField(verbose_name='post created time')),
                ('updated_time', models.DateTimeField(verbose_name='post updated time')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='runstat.GroupMember', verbose_name='author object id')),
            ],
        ),
        migrations.CreateModel(
            name='MemberTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tag', models.CharField(max_length=200, verbose_name='Tag mentioned in post')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='runstat.GroupMember', verbose_name='group member')),
            ],
        ),
        migrations.CreateModel(
            name='PostAttachments',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField(blank=True, max_length=1000, null=True)),
                ('title', models.TextField(blank=True, null=True)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='runstat.GroupPost', verbose_name='post id')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='membertag',
            unique_together=set([('author', 'tag')]),
        ),
    ]
