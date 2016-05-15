"""Views for runstat application."""
from django.shortcuts import render
from .models import GroupMember


def group_members(request):
    """Group Members list."""
    members = GroupMember.objects.all().order_by('object_id')[:50]
    return render(request, 'runstat/members.html', {'members': members})
