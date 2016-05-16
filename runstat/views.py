"""Views for runstat application."""
from django.shortcuts import render
from django.views.generic import TemplateView

from .models import GroupMember, GroupPost, PostAttachments


def group_members(request):
    """Group Members list."""
    # TODO: add pagination
    members = GroupMember.objects.all().order_by('object_id')[:50]
    return render(request, 'runstat/members.html', {'members': members})


def member(request, pk):
    """Return member page including all posts related."""
    context = {}
    member = GroupMember.objects.get(object_id=pk)
    context.update({'member': member})
    posts = GroupPost.objects.filter(author=pk)
    # add attachments to posts here
    context.update({'posts': posts})
    return render(request, 'runstat/member.html', context)


class AboutPage(TemplateView):
    """Return "About" page."""

    template_name = 'runstat/about.html'
