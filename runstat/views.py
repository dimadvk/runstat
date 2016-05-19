"""Views for runstat application."""
from django.shortcuts import render
from django.views.generic import TemplateView

from .models import GroupMember, GroupPost, MemberTag


def group_members(request):
    """Group Members list."""
    context = {}
    search_name = request.GET.get('search_name')
    if search_name:
        members = GroupMember.objects.filter(
            name__icontains=search_name).order_by('name')
    else:
        members = GroupMember.objects.all().order_by('name')
    context.update({'members': members})
    # add number of members
    context.update({'members_count': members.count()})
    return render(request, 'runstat/members.html', context)


def member(request, pk):
    """Return member page including all posts related."""
    context = {}
    # get member
    member = GroupMember.objects.get(object_id=pk)
    context.update({'member': member})
    # get posts of member
    posts = GroupPost.objects.filter(author=pk)
    context.update({'posts': posts})
    # get tags mentioned in posts
    tags = MemberTag.objects.filter(author_id=pk)
    tags = [x.tag for x in tags]
    context.update({'tags': tags})
    return render(request, 'runstat/member.html', context)


class AboutPage(TemplateView):
    """Return "About" page."""

    template_name = 'runstat/about.html'
