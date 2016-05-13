"""Models for runstat."""
from __future__ import unicode_literals

from django.db import models


class GroupMember(models.Model):
    """Model for group member."""

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
    photo = models.URLField(
        max_length=1000,
        default=''
    )


class GroupPost(models.Model):
    """Model for post in group feed."""

    object_id = models.CharField(
        verbose_name='post object id',
        unique=True,
        blank=False,
        max_length=100
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
        default='',
        null=True,
    )
    created_time = models.DateTimeField(
        verbose_name='post created time',
        null=False,
    )
    # TODO add 'has_attachment' BooleanField


class PostPhoto(models.Model):
    """Model for post photos."""

    object_id = models.BigIntegerField(
        verbose_name='post object id',
        unique=True,
        blank=False,
    )
    post_id = models.ForeignKey(
        'GroupPost',
        null=False,
        verbose_name='post',
        on_delete=models.CASCADE,
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
