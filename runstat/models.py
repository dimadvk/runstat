"""Models for runstat."""
from __future__ import unicode_literals

from django.db import models


class GroupMember(models.Model):
    """Model for group member."""

    object_id = models.BigIntegerField(
        verbose_name='member object id',
        unique=True,
        blank=False,
        primary_key=True,
    )
    name = models.CharField(
        verbose_name='member name',
        blank=False,
        max_length=256,
    )
    administrator = models.BooleanField()


class GroupPost(models.Model):
    """Model for post in group feed."""

    object_id = models.CharField(
        verbose_name='post object id',
        blank=False,
        max_length=100,
        unique=True,
    )
    author = models.BigIntegerField(
        verbose_name='author object id',
        blank=False,
    )
    message = models.TextField(
        blank=True,
        null=True,
        verbose_name='post message',
    )
    created_time = models.DateTimeField(
        verbose_name='post created time',
        null=False,
    )
    updated_time = models.DateTimeField(
        verbose_name='post updated time',
        null=True,
    )


class PostAttachments(models.Model):
    """Model for post attachments."""

    post = models.CharField(
        verbose_name='post object id',
        blank=False,
        max_length=100,
        unique=True,
    )
    url = models.URLField(
        max_length=1000,
        default=''
    )
    title = models.TextField(
        blank=True,
        default='',
    )
