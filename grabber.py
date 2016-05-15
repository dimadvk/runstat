"""Some tools used for getting data from Facebook."""
# -*- coding: utf-8 -*-
import os
import json
import facebook
import requests
import dateutil.parser
import MySQLdb
from pytz import utc


# constants
TOKEN_VALIDATION_URL = 'https://graph.facebook.com/oauth/access_token_info'
BASE_DIR = os.path.dirname(__file__)
TOKEN_FILE = os.path.join(BASE_DIR, '.fb_token')
SECRETS_FILE = os.path.join(BASE_DIR, 'root', 'secrets.json')
with open(SECRETS_FILE) as f:
    SECRETS = json.loads(f.read())
APP_ID = SECRETS['FACEBOOK_APP']['APP_ID']
APP_SECRET = SECRETS['FACEBOOK_APP']['APP_SECRET']
GROUP_ID = SECRETS['FACEBOOK_GROUP_ID']
# end const ##


def get_db(secrets=SECRETS):
    """Make a connection to database, return connection and cursor objects."""
    db = secrets['DATABASES']['default']
    if db['ENGINE'] == u'django.db.backends.mysql':
        connection = MySQLdb.connect(
            host=db['HOST'],
            user=db['USER'],
            passwd=db['PASSWORD'],
            db=db['NAME'],
            charset='utf8'
        )
    return connection, connection.cursor()


def get_access_token(graph_obj):
    """Return access_token as a string.

    Get token from file, validate. If not valid, get a new one.
    """
    # get token from file
    if os.path.isfile(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            access_token = f.read()
        # validate token
        response = requests.get(TOKEN_VALIDATION_URL, params={
            'client_id': APP_ID,
            'access_token': access_token})
        if response.status_code == 200:
            return access_token
    # if not valid or file don't exists, get a new one
    access_token = graph_obj.get_app_access_token(APP_ID, APP_SECRET)
    # and save the token to file
    with open(TOKEN_FILE, 'w+') as f:
        f.write(access_token)
    return access_token


def get_group_members(graph_obj, group_id):
    """Return a list of group members."""
    members_page = graph_obj.get_connections(
        id=group_id, connection_name='members', **{'limit': '100'})
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


def renew_group_members(graph_obj, group_id):
    """Renew group members list in database."""
    # get group members from fb

    # get group members from db

    # make the diff: some body can join group, somebody leave.
    # Somebody could change name or became admin

    # write changes to db. May be make column object_id 'UNIQUE'
    # or user 'INSERT OR REPLACE'

    # to recognize who leave group:
    # list(set(members_db) - set(members_fb))

    return True


def get_group_posts(graph_obj, group_id):
    """Get all posts from group feed."""
    kwargs = {'fields': 'id,from,updated_time,created_time,message,attachments',
              'limit': 200}
    posts_page = graph_obj.get_connections(
        id=group_id, connection_name='feed', **kwargs)
    posts_list = posts_page.get('data', [])
    while True:
        if ('paging' in posts_page.keys() and
                'next' in posts_page['paging'].keys()):
                url_next_page = posts_page['paging'].get('next')
        else:
            break
        posts_page = requests.get(url_next_page).json()
        posts_list.extend(posts_page.get('data', []))

    posts_pretty_list = []
    for post in posts_list:
        # check attachment
        attachments = get_attachments(post)
        created_time = dateutil.parser.parse(post.get('created_time'))
        created_time = created_time.astimezone(utc).replace(tzinfo=None)
        updated_time = dateutil.parser.parse(post.get('updated_time'))
        updated_time = updated_time.astimezone(utc).replace(tzinfo=None)
        message = post.get('message', '')
        message = message.encode('unicode_escape')
        posts_pretty_list.append({
            'object_id': post.get('id'),
            'author': post.get('from').get('id'),
            'created_time': created_time,
            'updated_time': updated_time,
            'message': message,
            'attachments': attachments
        })
    return posts_pretty_list


def get_attachments(post):
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
        title = post['attachments']['data'][0]['title'].encode('unicode_escape')
    except:
        pass
    if 'attachments' in post.keys() and not links and not title:
        title = 'Attachments exists, but undefined'
    return {'links': links, 'title': title}


if __name__ == '__main__':
    # database
    db_conn, db_cursor = get_db()

    # create GraphAPI instance
    graph = facebook.GraphAPI(version='2.5')
    graph.access_token = get_access_token(graph)

    # Do the deal

    # grab group members
    members = get_group_members(graph, GROUP_ID)
    for member in members:
        db_cursor.execute(
            """replace into runstat_groupmember
                    (object_id, name, administrator)
                        values (%s, %s, %s)""",
            (member['id'],
             member['name'],
             member['administrator']))
    db_conn.commit()

    # grab group posts
    posts = get_group_posts(graph, GROUP_ID)
    for post in posts:
        # write posts
        db_cursor.execute(
            """replace into runstat_grouppost
                  (object_id, author, created_time, updated_time, message)
                        values (%s, %s, %s, %s, %s)""",
            (post['object_id'],
             post['author'],
             post['created_time'],
             post['updated_time'],
             post['message']))
    db_conn.commit()
    # write attachments information
    for post in posts:
        for link in post['attachments']['links']:
            db_cursor.execute(
                """replace into runstat_postattachments
                    (post, url, title) values (%s, %s, %s)""",
                (post['object_id'],
                 link,
                 post['attachments']['title'])
            )
    db_conn.commit()

    # grab post photos
    # photos = get_post_photos(graph, GROUP_ID)

    # close database connection
    db_conn.close()
