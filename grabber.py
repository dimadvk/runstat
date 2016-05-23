"""Some tools used for getting data from Facebook."""
# -*- coding: utf-8 -*-
import os
import json
import facebook
import requests
import dateutil.parser
import MySQLdb
from pytz import utc
import re


# constants
BASE_DIR = os.path.dirname(__file__)
TOKEN_VALIDATION_URL = 'https://graph.facebook.com/oauth/access_token_info'
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
    # get unixtime of last post
    if query_result:
        last_post_time = query_result[0]
        since = str(int(last_post_time.strftime('%s')) - 3600)
    else:
        since = '0'
    # make a query to facebook with 'since' parametr
    fields = 'id,from,updated_time,created_time,message,attachments'
    kwargs = {'fields': fields, 'limit': 100, 'since': since}
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
    print "Count received posts: ", len(posts_list)
    posts_pretty_list = []
    for post in posts_list:
        # check attachment
        attachments = get_attachments(post)
        created_time = dateutil.parser.parse(post.get('created_time'))
        created_time = created_time.astimezone(utc).replace(tzinfo=None)
        updated_time = dateutil.parser.parse(post.get('updated_time'))
        updated_time = updated_time.astimezone(utc).replace(tzinfo=None)
        message = post.get('message', '')
        # message = message.encode('unicode_escape')
        message = message.encode('utf-8')
        posts_pretty_list.append({
            'object_id': post.get('id'),
            'author': post.get('from').get('id'),
            'created_time': created_time,
            'updated_time': updated_time,
            'message': message,
            'attachments': attachments
        })

    # get list of members id from database
    db_curs.execute('select object_id from runstat_groupmember')
    result = db_curs.fetchall()
    members_id_list = [str(m[0]) for m in result]
    # write received posts to database
    for post in posts_pretty_list:
        if post['author'] not in members_id_list:
            continue
        db_curs.execute(
            "select 1 from runstat_grouppost where object_id=%s",
            (post['object_id'], )
        )
        post_id = db_curs.fetchone()
        if post_id:
            db_curs.execute(
                "delete from runstat_postattachments where post_id=%s",
                (post_id, )
            )
        db_curs.execute(
            """replace into runstat_grouppost
                  (object_id, author_id, created_time, updated_time, message)
                        values (%s, %s, %s, %s, %s)""",
            (post['object_id'],
             post['author'],
             post['created_time'],
             post['updated_time'],
             post['message']))
        # and write attachments info to database
        links = post['attachments']['links']
        post_id = str(db_curs.lastrowid)
        if len(links) == 0:
            db_curs.execute(
                """insert into runstat_postattachments (post_id, title)
                    values (%s, %s)""",
                (post_id, post['attachments']['title'])
            )
        else:
            for link in links:
                db_curs.execute(
                    """insert into runstat_postattachments
                        (post_id, url, title) values (%s, %s, %s)""",
                    (post_id,
                     link,
                     post['attachments']['title'])
                )
    # write posts tags
    db_conn.commit()
    db_conn.close()
    write_posts_tags(posts_pretty_list)


def write_posts_tags(posts):
    """Get list of posts, collect tags from messages and write to database."""
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
    db_conn, db_curs = get_db()
    for el in members_tags:
        # check if authos is still a member of the group
        db_curs.execute(
            """select count(object_id) from runstat_groupmember
                where object_id=%s""",
            (el['author'], )
        )
        count = db_curs.fetchone()[0]
        if count == 1:
            for tag in el['tags']:
                db_curs.execute(
                    """replace into runstat_membertag (author_id, tag)
                        values (%s, %s)""",
                    (el['author'], tag)
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
        message = message.encode('utf-8', 'unicode_escape')
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
        title = post['attachments']['data'][0]['title'].encode(
            'utf-8', 'unicode_escape')
    except:
        pass
    if 'attachments' in post.keys() and not links and not title:
        title = 'Attachments exists, but undefined'
    return {'links': links, 'title': title}


if __name__ == '__main__':
    # create GraphAPI instance
    graph = facebook.GraphAPI(version='2.5')
    graph.access_token = get_access_token(graph)

    # grab group posts
    renew_group_posts(graph, GROUP_ID)
