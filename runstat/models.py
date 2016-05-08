from __future__ import unicode_literals

from django.db import models


class GroupMember(models.Model):

    object_id = models.BigIntegerField(
        verbose_name='member object id',
        unique=True,
        blank=False,
    )
    name = models.CharField(
        verbose_name='member name',
        blank=False,
        max_length=256,
    )
    administrator = models.BooleanField()


class GroupPost(models.Model):

    object_id = models.BigIntegerField(
        verbose_name='post object id',
        unique=True,
        blank=False,
    )

    author = models.ForeignKey(
        'GroupMember',
        verbose_name='post author',
        null=True,
        on_delete=models.SET_NULL,
    )
    message = models.TextField(
        blank=True,
        null=True,
        verbose_name='post message',
    )
    tags = models.CharField(
        verbose_name='tags in post',
        max_length=4096,
        blank=True,
    )

class PostPhoto(models.Model):

    object_id = models.BigIntegerField(
        verbose_name='post object id',
        unique=True,
        blank=False,
    )
    url_native = models.URLField(
        max_length=1000
    )
    url_x600 = models.URLField(
        max_length=1000
    )
    url_x480 = models.URLField(
        max_length=1000
    )
