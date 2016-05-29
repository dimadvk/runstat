"""Views for runstat application."""
from django.shortcuts import render
from django.views.generic import TemplateView
from django.db.models import Count
from django.shortcuts import get_object_or_404

from .models import GroupMember, GroupPost, MemberTag


def group_members(request):
    """Group Members list."""
    context = {}
    search_name = request.GET.get('search_name')
    if search_name:
        members = GroupMember.objects.filter(
            name__icontains=search_name).annotate(
                posts_count = Count('grouppost')).order_by('-posts_count')
    else:
        members = GroupMember.objects.annotate(
            posts_count = Count('grouppost')).order_by('-posts_count')
    context.update({'members': members})
    # add number of members
    context.update({'members_count': members.count()})
    # add posts_num
    object_id = '1143756885657529'
    posts_num = {object_id: '25'}
    context.update({'object_id': object_id, 'posts_num': posts_num})
    return render(request, 'runstat/members.html', context)


def member(request, pk):
    """Return member page including all posts related."""
    context = {}
    # get member
    member = get_object_or_404(GroupMember, object_id=pk)
    context.update({'member': member})
    # get posts of member
    posts = GroupPost.objects.filter(author=pk).order_by('-created_time')
    context.update({'posts': posts})
    # get tags mentioned in posts
    tags = MemberTag.objects.filter(author_id=pk)
    tags = [x.tag for x in tags]
    context.update({'tags': tags})
    return render(request, 'runstat/member.html', context)


class AboutPage(TemplateView):
    """Return "About" page."""

    template_name = 'runstat/about.html'
