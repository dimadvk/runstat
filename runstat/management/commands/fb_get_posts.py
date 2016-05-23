"""Management command for getting posts from feed of facebook group."""
import os
import re
import json
import facebook
import requests
import dateutil.parser
from pytz import utc
from datetime import timedelta

from django.core.management import BaseCommand
from django.conf import settings

from runstat.models import GroupPost, PostAttachments, MemberTag, GroupMember


class Command(BaseCommand):
    """Renew list of members of facebook group."""

    # TODO: have to cpecify options to set 'since' parametr
    # without 'since' specified script gets last 'updated time' from db
    # args = '<--since=UNIXTIME, --limit=NUM>'
    # args = ['--since=UNIXTIME',]
    help = "Get posts from feed of facebook group."

    def add_arguments(self, parser):
        """Add optional arguments for command."""
        parser.add_argument(
            '--limit',
            action='store',
            dest='limit',
            default=False,
            help='Maximum number of posts per page in API-query',
        )
        parser.add_argument(
            '--since',
            action='store',
            dest='since',
            default=False,
            help='Maximum number of posts per page in API-query',
        )

    BASE_DIR = settings.BASE_DIR
    TOKEN_VALIDATION_URL = 'https://graph.facebook.com/oauth/access_token_info'
    TOKEN_FILE = os.path.join(BASE_DIR, '.fb_token')
    SECRETS_FILE = os.path.join(BASE_DIR, 'root', 'secrets.json')

    def _get_secrets(secrets_file):
        """Return dict with secrets from file."""
        with open(secrets_file) as f:
            secrets = json.loads(f.read())
        return secrets

    SECRETS = _get_secrets(SECRETS_FILE)
    APP_ID = SECRETS['FACEBOOK_APP']['APP_ID']
    APP_SECRET = SECRETS['FACEBOOK_APP']['APP_SECRET']
    GROUP_ID = SECRETS['FACEBOOK_GROUP_ID']
    POSTS_NUM_LIMIT = '100'

    def _get_graph_object(self):
        """Return instance of GraphAPI with access tocken set."""
        graph = facebook.GraphAPI(version='2.5')
        graph.access_token = self._get_access_token(graph)
        return graph

    def _get_access_token(self, graph_obj):
        """Return access_token as a string.

        Get token from file, validate. If not valid, get a new one.
        """
        # get token from file
        if os.path.isfile(self.TOKEN_FILE):
            with open(self.TOKEN_FILE, 'r') as f:
                access_token = f.read()
            # validate token
            response = requests.get(self.TOKEN_VALIDATION_URL, params={
                'client_id': self.APP_ID,
                'access_token': access_token})
            if response.status_code == 200:
                return access_token
        # if token not valid or file does not exist, get a new one
        access_token = graph_obj.get_app_access_token(
            self.APP_ID, self.APP_SECRET)
        # and save the token to file
        with open(self.TOKEN_FILE, 'w+') as f:
            f.write(access_token)
        return access_token

    def _get_attachments(self, post):
        """Try to get subattachemnts from post."""
        links = []
        try:
            for l in post['attachments']['data'][0]['subattachments']['data']:
                links.append(l['media']['image']['src'])
        except:
            pass
        if not links:
            try:
                links.append(
                    post['attachments']['data'][0]['media']['image']['src'])
            except:
                pass
        title = ''
        try:
            title = post['attachments']['data'][0]['title'].encode(
                'utf-8', 'unicode_escape')
        except:
            pass
        if 'attachments' in post.keys() and not links and not title:
            title = 'Attachments exists, but undefined'
        return {'links': links, 'title': title}

    def _get_posts_from_fb(self, options):
        """Return list of posts from fb-group feed."""
        graph = self._get_graph_object()
        # get limit option
        limit = options.get('limit')
        if not limit:
            limit = self.POSTS_NUM_LIMIT
        # get 'since' option
        since = options.get('since')
        # if not since get 'updated time' of last post in database
        if not since:
            try:
                last_post = GroupPost.objects.order_by('-updated_time')[0]
                since = last_post.updated_time - timedelta(hours=1)
                since = since.strftime('%s')
            except:
                since = '0'
        print "Options: limit={}, since={}".format(limit, since)
        # make a query to facebook with 'since' parametr
        fields = 'id,from,updated_time,created_time,message,attachments'
        kwargs = {'fields': fields, 'limit': limit, 'since': since}
        posts_page = graph.get_connections(
            id=self.GROUP_ID, connection_name='feed', **kwargs)
        posts_list = posts_page.get('data', [])
        while True:
            if ('paging' in posts_page.keys() and
                    'next' in posts_page['paging'].keys()):
                    url_next_page = posts_page['paging'].get('next')
            else:
                break
            posts_page = requests.get(url_next_page).json()
            posts_list.extend(posts_page.get('data', []))
        print "Count of received posts: ", len(posts_list)
        posts_pretty_list = []
        for post in posts_list:
            # check attachment
            attachments = self._get_attachments(post)
            created_time = dateutil.parser.parse(post.get('created_time'))
            # created_time = created_time.astimezone(utc).replace(tzinfo=None)
            updated_time = dateutil.parser.parse(post.get('updated_time'))
            # updated_time = updated_time.astimezone(utc).replace(tzinfo=None)
            message = post.get('message', '')
            message = message.encode('utf-8')
            posts_pretty_list.append({
                'object_id': post.get('id'),
                'author': post.get('from').get('id'),
                'created_time': created_time,
                'updated_time': updated_time,
                'message': message,
                'attachments': attachments
            })
        return posts_pretty_list

    def _write_attachments_info(self, fb_post, db_post):
        """Write to database info about attachments of post."""
        links = fb_post['attachments']['links']
        if len(links) == 0:
            PostAttachments.objects.create(
                post=db_post,
                title=fb_post['attachments']['title']
            )
        else:
            for link in links:
                PostAttachments.objects.create(
                    post=db_post,
                    url=link,
                    title=fb_post['attachments']['title']
                )

    def _write_posts_tags(self, posts):
        """Collect tags from posts messages and write to database."""
        # make list of dicts {'author': 'tags'}
        members_tags = []
        for post in posts:
            tags = re.findall(
                re.compile(r'\#(\w+)', re.IGNORECASE|re.U),
                post['message'].decode('utf8'),
            )
            members_tags.append(
                {'author': post['author'],
                 'tags': tags}
            )
        # write tags to database
        for el in members_tags:
            for tag in el['tags']:
                try:
                    MemberTag.objects.create(
                        author=GroupMember.objects.get(object_id=el['author']),
                        tag=tag,
                    )
                except:
                    continue

    def handle(self, *args, **options):
        """Get posts from group feed and write to database."""
        # get posts_list from facebook group
        posts_list = self._get_posts_from_fb(options)
        # write received posts to database
        for fb_post in posts_list:
            get_author = GroupMember.objects.filter(
                object_id=fb_post['author'])
            if len(get_author):
                db_post, created = GroupPost.objects.update_or_create(
                    object_id=fb_post['object_id'],
                    author=get_author[0],
                    defaults={
                        'created_time': fb_post['created_time'],
                        'updated_time': fb_post['updated_time'],
                        'message': fb_post['message'],
                    }
                )
            # except:
            #     continue
            # and write attachments info to database
            if created:
                self._write_attachments_info(fb_post, db_post)
        # # write posts tags
        self._write_posts_tags(posts_list)
