"""Views for runstat application."""
from django.shortcuts import render
from django.views.generic import TemplateView

from .models import GroupMember, GroupPost


def group_members(request):
    """Group Members list."""
    search_name = request.GET.get('search_name')
    if search_name:
        members = GroupMember.objects.filter(
            name__contains=search_name).order_by('name')
    else:
        members = GroupMember.objects.all().order_by('name')
    return render(request, 'runstat/members.html', {'members': members})


def member(request, pk):
    """Return member page including all posts related."""
    context = {}
    member = GroupMember.objects.get(object_id=pk)
    context.update({'member': member})
    posts = GroupPost.objects.filter(author=pk)
    # add attachments to posts here
    context.update({'posts': posts})
    for post in posts:
        print post.object_id, post.message
    return render(request, 'runstat/member.html', context)


class AboutPage(TemplateView):
    """Return "About" page."""

    template_name = 'runstat/about.html'
