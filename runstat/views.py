"""Views for runstat application."""
from qsstats import QuerySetStats
from datetime import datetime
import pytz

from django.shortcuts import render, render_to_response
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
                posts_count=Count('grouppost')).order_by('-posts_count')
    else:
        members = GroupMember.objects.annotate(
            posts_count=Count('grouppost')).order_by('-posts_count')
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


def statistic(request):
    """Return statistic page."""
    template = 'runstat/statistic.html'
    tzkiev = pytz.timezone('Europe/Kiev')
    start_date = tzkiev.localize(datetime.strptime('2016-05-01', '%Y-%m-%d'))
    end_date = tzkiev.localize(datetime.strptime('2016-06-01', '%Y-%m-%d'))
    # count of deposits
    deposits_amount = 759
    # datetime of last update
    actual_date = GroupPost.objects.order_by(
        'updated_time').values('updated_time').last()
    actual_date = actual_date['updated_time']
    # count of all members
    members_amount = GroupMember.objects.all().count()
    # count of members who got finished
    members_finished_amount = GroupMember.objects.all().annotate(
        posts_count=Count('grouppost')).filter(posts_count__gte=12).count()
    # count members who got out of race
    members_fail_amount = deposits_amount - members_finished_amount
    # approximate money profit
    profit = members_fail_amount*100/members_finished_amount
    # count of members who join the group but didn't run
    onlookers_amount = GroupMember.objects.all().annotate(
        posts_count=Count('grouppost')).filter(posts_count__lte=1).count()
    # members_age
    # day time of runs
    # count of posts per day
    # {'date_created': datetime.date(2016, 5, 28), 'posts_count': 328}
    # posts_per_day = GroupPost.objects.all().extra({
    #    'date_created': 'date(convert_tz(created_time, "GMT", "Europe/Kiev"))'
    #    }).values('date_created').annotate(posts_count=Count('object_id'))
    # tzkiev = pytz.timezone('Europe/Kiev')
    # start_date = datetime.strptime('2016-05-01', '%Y-%m-%d')
    # start_date = tzkiev.localize(start_date)
    # end_date = datetime.strptime('2016-05-31', '%Y-%m-%d')
    # end_date = tzkiev.localize(end_date)
    # start_date = datetime.strptime('2016-05-01', '%Y-%m-%d').date()
    # end_date = datetime.strptime('2016-06-01', '%Y-%m-%d').date()
    qs = GroupPost.objects.all()
    qss = QuerySetStats(qs, date_field='created_time')
    values = qss.time_series(start_date, end_date, interval='days')
    # for el in qs:
    #     el.created_time = el.created_time.datetime.astimezone(
    #         pytz.timezone('Europe/Kiev'))
    # qss = QuerySetStats(qs, date_field='created_time')
    values = GroupPost.objects.filter(created_time__range=(start_date, end_date)).extra({'date_created': 'date(convert_tz(created_time, "GMT", "Europe/Kiev"))'}).values('date_created').annotate(posts_count=Count('object_id')).order_by('date_created')

    context = {
        'deposits_amount': deposits_amount,
        'actual_date': actual_date,
        'onlookers_amount': onlookers_amount,
        'members_amount': members_amount,
        'members_finished_amount': members_finished_amount,
        'members_fail_amount': members_fail_amount,
        'profit': profit,
        'values': values,
    }
    return render(request, template, context)


def test(request):
    """Just test page."""
    template_name = 'runstat/test.html'
    #
    start_date = datetime.strptime('2016-05-01', '%Y-%m-%d').date()
    end_date = datetime.strptime('2016-05-31', '%Y-%m-%d').date()
    qs = GroupPost.objects.all()
    qss = QuerySetStats(qs, date_field='created_time')
    values = qss.time_series(start_date, end_date, interval='days')

    return render(request, template_name, {'values': values})
