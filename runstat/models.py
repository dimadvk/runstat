"""Models for runstat."""
from __future__ import unicode_literals

from django.db import models


class GroupMember(models.Model):
    """Model for group member."""

    SEX_CHOICES = (
        ('m', 'male'),
        ('f', 'female'),
    )

    object_id = models.BigIntegerField(
        verbose_name='member object id',
        unique=True,
        blank=False,
        primary_key=True,
    )
    name = models.CharField(
        verbose_name='member name',
        blank=False,
        max_length=255,
    )
    administrator = models.BooleanField
    sex = models.CharField(
        verbose_name="sex of a member",
        blank=True,
        null=True,
        max_length=1,
        choices=SEX_CHOICES,
        default=None,
    )
    age = models.PositiveSmallIntegerField(
        verbose_name="age of a member",
        blank=True,
        null=True,
    )


class MemberTag(models.Model):
    """Model for tags which member mentioned in posts."""

    class Meta:
        unique_together = ('author', 'tag')

    author = models.ForeignKey(
        'GroupMember',
        on_delete=models.CASCADE,
        verbose_name='group member'
    )
    tag = models.CharField(
        max_length=200,
        verbose_name='Tag mentioned in post',
    )


class GroupPost(models.Model):
    """Model for post in group feed."""

    object_id = models.CharField(
        verbose_name='post object id',
        blank=False,
        max_length=100,
        unique=True,
    )
    author = models.ForeignKey(
        'GroupMember',
        verbose_name='author object id',
        on_delete=models.CASCADE,
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
        null=False,
    )


class PostAttachments(models.Model):
    """Model for post attachments."""

    post = models.ForeignKey(
        'GroupPost',
        verbose_name='post id',
        on_delete=models.CASCADE,
    )
    url = models.URLField(
        max_length=1000,
        blank=True,
        null=True,
    )
    attach_type = models.TextField(
        blank=True,
        null=True,
        verbose_name="Attachments type"
    )
