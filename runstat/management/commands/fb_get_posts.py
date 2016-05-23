"""Management command for getting posts from feed of facebook group."""
import os
import json
import facebook
import requests
from optparse import make_option
import dateutil.parser
from pytz import utc
import re

from django.core.management import BaseCommand
from django.conf import settings

from runstat.models import GroupPost, PostAttachments, MemberTag


class Command(BaseCommand):
    """Renew list of members of facebook group."""

    # TODO: have to cpecify options to set 'since' parametr
    # without 'since' specified script gets last 'updated time' from db
    args = '--since=UNIXTIME, --limit=NUM'
    help = "Get posts from feed of facebook group."

    option_list = BaseCommand.option_list + (
        make_option(
            '--since',
            action='store',
            dest='since',
            help='Unixtime posts should be get from"',
        ),
        make_option(
            '--limit',
            action='store',
            dest='limit',
            help='Maximum number of posts per page in API-query',
        )
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
            limit = 100
        # get 'since' option
        since = options.get('since')
        # if not since get 'updated time' of last post in database
        if not since:
            try:
                last_post = GroupPost.objects.order_by('-updated_time')[0]
                since = last_post.updated_time.strftime('%s')
            except:
                since = '0'
        # make a query to facebook with 'since' parametr
        fields = 'id,from,updated_time,created_time,message,attachments'
        kwargs = {'fields': fields, 'limit': 100, 'since': since}
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
            created_time = created_time.astimezone(utc).replace(tzinfo=None)
            updated_time = dateutil.parser.parse(post.get('updated_time'))
            updated_time = updated_time.astimezone(utc).replace(tzinfo=None)
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

    def handle(self, *args, **options):
        """Get posts from group feed and write to database."""
        # get posts_list from facebook group
        posts_list = self._get_posts_from_fb(options)
        # write received posts to database
        for fb_post in posts_list:
            db_post, created = GroupPost.objcets.update_or_create(
                object_id=post['object_id'],
                author=post['author'],
                created_time=post['created_time'],
                updated_time=post['updated_time'],
                message=post['message'])
            )
            # and write attachments info to database
            links = fb_post['attachments']['links']
            if len(links) == 0:
                db_curs.execute(
                    """insert into runstat_postattachments (post_id, title)
                        values (%s, %s)""",
                    (post_id, post['attachments']['title'])
                )
                PostAttachments.
            else:
                for link in links:
                    db_curs.execute(
                        """insert into runstat_postattachments
                            (post_id, url, title) values (%s, %s, %s)""",
                        (post_id,
                         link,
                         post['attachments']['title'])
                    )
        # # write posts tags
        write_posts_tags(posts_list)
