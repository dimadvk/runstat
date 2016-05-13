"""Some tools used for getting data from Facebook."""
# -*- coding: utf-8 -*-
import os
import sqlite3
import facebook
import requests
import dateutil.parser


# constants
APP_ID = '542329375940973'
APP_SECRET = '36b075370d6f7e06ac4d225d3d2d3f6d'
# 'Pobezhali' group id
GROUP_ID = '1745974432290684'
TOKEN_VALIDATION_URL = 'https://graph.facebook.com/oauth/access_token_info'
BASE_DIR = os.path.dirname(__file__)
TOKEN_FILE = os.path.join(BASE_DIR, '.fb_token')
DATABASE = os.path.join(BASE_DIR, 'run.sqlite3')
# end const ##


def execute_sql(database, statement, args=()):
    """
    Execute SQL-statement, return result.

    Next format of oraguments is required:
      'statement' - sql-statement as a string, 'args' - tuple.
    """
    with sqlite3.connect(database) as connection:
        curs = connection.cursor()
        # Foreign key constraints are disabled by default,
        # so must be enabled separately for each database connection
        curs.execute('PRAGMA FOREIGN_KEYS=ON')
        curs.execute(statement, args)
    return curs.fetchall()


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
        id=group_id, connection_name='members')
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
    kwargs = {'fields': 'id,from,updated_time,message', 'limit': 100}
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
        posts_pretty_list.append({
            'object_id': post.get('id'),
            'author': post.get('from').get('id'),
            'created_time': dateutil.parser.parse(post.get('updated_time')),
            'message': post.get('message'),
        })
    return posts_pretty_list


def get_post_photos(graph_obj, group_id):
    """Get attached photos of all posts in group feed."""
    # get list of post_id from db
    # for every post_id:
    #   if no entry in db for this post id, then make a query
    return []

if __name__ == '__main__':
    # database
    if not os.path.isfile(DATABASE):
        print "ERROR: database not found"
        exit()
    db_connection = sqlite3.connect(DATABASE)
    db_cursor = db_connection.cursor()

    # create GraphAPI instance
    graph = facebook.GraphAPI(version='2.5')
    graph.access_token = get_access_token(graph)

    # Do the deal

    # grab group members
    # members = get_group_members(graph, GROUP_ID)
    # for member in members:
    #     db_cursor.execute('insert or replace into runstat_groupmember \
    #                       (object_id, name, administrator) \
    #                       values (?, ?, ?)',
    #                       (member['id'],
    #                        member['name'],
    #                        member['administrator']))
    # db_connection.commit()

    # grab group posts
    posts = get_group_posts(graph, GROUP_ID)
    for post in posts:
        db_cursor.execute('insert or replace into runstat_grouppost \
                          (object_id, author_id, created_time, message) \
                          values (?, ?, ?, ?)',
                          (post['object_id'],
                           post['author'],
                           post['created_time'],
                           post['message']))
    db_connection.commit()

    # grab post photos
    photos = get_post_photos(graph, GROUP_ID)

    # close database connection
    db_connection.close()
