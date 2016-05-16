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
    members_fb = get_group_members(graph_obj, group_id)
    members_fb_id = [m['id'] for m in members_fb]

    # get group members from db
    db_conn, db_curs = get_db()
    db_curs.execute('select object_id from runstat_groupmember')
    members_db = db_curs.fetchall()
    members_db_id = [str(m[0]) for m in members_db]

    # make the diff: some body can join group, somebody leave.
    # Ignore any changes in member's name or admin status
    left_the_group = set(members_db_id) - set(members_fb_id)
    join_the_group = set(members_fb_id) - set(members_db_id)
    joined_members = []
    for member in members_fb:
        if member['id'] in join_the_group:
            joined_members.append(member)

    # write changes to db
    for member in left_the_group:
        db_curs.execute(
            'delete from runstat_groupmember where object_id=%s',
            (member, )
        )
    for member in joined_members:
        db_curs.execute(
            """insert into runstat_groupmember (object_id, name, administrator)
                values (%s, %s, %s)""",
            (member['id'],
             member['name'],
             member['administrator'])
        )
    db_conn.commit()
    db_conn.close()


def renew_group_posts(graph_obj, group_id):
    """Add to database new posts from group newsfeed."""
    # get database connection
    db_conn, db_curs = get_db()
    # get 'updated time' of last post in database
    db_curs.execute(
        """select updated_time from runstat_grouppost
            order by updated_time desc limit 1"""
    )
    query_result = db_curs.fetchone()
    # get unixtime-60seconds of last post
    if query_result:
        last_post_time = query_result[0]
        since = str(int(last_post_time.strftime('%s')) - 60)
    else:
        since = '0'
    # make a query to facebook with 'since' parametr
    fields = 'id,from,updated_time,created_time,message,attachments'
    kwargs = {'fields': fields, 'limit': 200, 'since': since}
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

    # write received posts to database
    # write posts
    for post in posts_pretty_list:
        db_curs.execute(
            """replace into runstat_grouppost
                  (object_id, author, created_time, updated_time, message)
                        values (%s, %s, %s, %s, %s)""",
            (post['object_id'],
             post['author'],
             post['created_time'],
             post['updated_time'],
             post['message']))
        # and write attachments info to database
        links = post['attachments']['links']
        # delete old attachments for post and write recently received info
        db_curs.execute(
            "delete from runstat_postattachments where post_id=%s",
            (post['object_id'], )
        )
        if len(links) == 0:
            db_curs.execute(
                """insert into runstat_postattachments (post_id, title)
                    values (%s, %s)""",
                (post['object_id'], post['attachments']['title'])
            )
        else:
            for link in links:
                db_curs.execute(
                    """replace into runstat_postattachments
                        (post_id, url, title) values (%s, %s, %s)""",
                    (post['object_id'],
                     link,
                     post['attachments']['title'])
                )
    db_conn.commit()
    db_conn.close()


def get_group_posts(graph_obj, group_id):
    """Get all posts from group feed."""
    fields = 'id,from,updated_time,created_time,message,attachments'
    kwargs = {'fields': fields, 'limit': 200}
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
    # create GraphAPI instance
    graph = facebook.GraphAPI(version='2.5')
    graph.access_token = get_access_token(graph)

    # Do the deal

    # grab group members
    renew_group_members(graph, GROUP_ID)

    # grab group posts
    renew_group_posts(graph, GROUP_ID)
