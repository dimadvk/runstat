"""Views for runstat application."""
from django.shortcuts import render
from .models import GroupMember


def group_members(request):
    """Group Members list."""
    members = GroupMember.objects.filter(id__lt=50).order_by('id')
    return render(request, 'runstat/members.html', {'members': members})
