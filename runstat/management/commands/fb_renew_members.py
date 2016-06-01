"""Management command for getting list of members from facebook group."""
import os
import json
import facebook
import requests

from django.core.management import BaseCommand
from django.conf import settings

from runstat.models import GroupMember


class Command(BaseCommand):
    """Renew list of members of facebook group."""

    args = ''
    help = "Get all members from facebook group and write to database."

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

    def _get_group_members(self, graph_obj):
        """Return a list of group members."""
        members_page = graph_obj.get_connections(
            id=self.GROUP_ID, connection_name='members', **{'limit': '100'})
        members_list = members_page.get('data', [])
        while True:
            if ('paging' in members_page.keys() and
                    'next' in members_page['paging'].keys()):
                    url_next_page = members_page['paging'].get('next')
            else:
                break
            members_page = requests.get(url_next_page).json()
            members_list.extend(members_page.get('data', []))

        return members_list

    def handle(self, *args, **options):
        """Renew group members list in database."""
        # get group members from fb
        graph = self._get_graph_object()
        members_fb = self._get_group_members(graph)
        members_fb_id = [m['id'] for m in members_fb]

        # get list of id of group members from database
        members_db_id = GroupMember.objects.values_list('object_id')
        members_db_id = [str(id[0]) for id in members_db_id]

        print "Members nums:"
        print "- got from FB: %d" % len(members_fb_id)
        print "- got from DB: %d" % len(members_db_id)

        # make the diff: some body can join group, somebody leave.
        left_the_group = set(members_db_id) - set(members_fb_id)
        join_the_group = set(members_fb_id) - set(members_db_id)
        joined_members = []
        for member in members_fb:
            if member['id'] in join_the_group:
                joined_members.append(member)

        # write changes to db
        # delete members which left the group
        GroupMember.objects.filter(object_id__in=left_the_group).delete()
        # save new members
        for member in joined_members:
            GroupMember.objects.create(
                object_id=member['id'],
                name=member['name'],
                # administrator=member['administrator'],
            )
        # update info of members (may be some change a name or "administrator")
        for member in members_fb:
            GroupMember.objects.filter(object_id=member['id']).update(
                name=member['name'],
                # administrator=member['administrator'],
            )
