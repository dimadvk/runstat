"""Some tools used for getting data from Facebook"""
# -*- coding: utf-8 -*-
import os
import sqlite3
import facebook
import requests



## const ##
APP_ID = '542329375940973'
APP_SECRET = '36b075370d6f7e06ac4d225d3d2d3f6d'
TOKEN_VALIDATION_URL = 'https://graph.facebook.com/oauth/access_token_info'
BASE_DIR = os.path.dirname(__file__)
TOKEN_FILE = os.path.join(BASE_DIR, '.fb_token')
DATABASE = os.path.join(BASE_DIR, 'run.sqlite3')
## end const ##


def execute_sql(db, statement, args=()):
    """
    Execute SQL-statement, return result.
    Next format of oraguments is required: 
      'statement' - sql-statement as a string, 'args' - tuple.
    """
    with sqlite3.connect(db) as connection:
        curs = connection.cursor()
        # Foreign key constraints are disabled by default, 
        # so must be enabled separately for each database connection
        curs.execute('PRAGMA FOREIGN_KEYS=ON')
        curs.execute(statement, args)
    return curs.fetchall()


def get_access_token(graph_obj):
    """Get token from file, validate. If not valid, get a new one. \
            Return access_token as a string"""
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
    """Return a list of group members"""
    members_page = graph_obj.get_connections(
        id=group_id, connection_name='members')
    members = members_page.get('data', [])
    while True:
        url_next_page = members_page['paging'].get('next')
        if not url_next_page:
            break
        members_page = requests.get(url_next_page).json()
        members.extend(members_page.get('data', []))

    return members

def renew_group_members(graph_obj, group_id):
    """Renew group members list in database"""
    # get group members from fb

    # get group members from db

    # make the diff: some body can join group, somebody leave. 
    # Somebody could change name or became admin

    # write changes to db. May be make column object_id 'UNIQUE'
    # or user 'INSERT OR REPLACE'

    # to recognize who leave group:
        # list(set(members_db) - set(members_fb))

    return True


if __name__ == '__main__':
    # database 
    if not os.path.isfile(DATABASE):
        with sqlite3.connect(DATABASE) as conn:
            conn.executescript('''
                    CREATE TABLE members
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         object_id INTEGER,
                         name TEXT,
                         administrator INTEGER,
                         UNIQUE(object_id));
                    ''')

    # create GraphAPI instance
    graph = facebook.GraphAPI(version='2.5')
    graph.access_token = get_access_token(graph)

    group_id = '1745974432290684'
    members = get_group_members(graph, group_id)
    print "Lenght: ", len(members)

    conn = sqlite3.connect(DATABASE)
    for member in members:
        print member
        conn.execute('insert or replace into members (object_id, name, administrator) \
                     values (?, ?, ?)',
                     (member['id'],
                      member['name'],
                      member['administrator']))
    conn.commit()
    conn.close()
#        execute_sql(
#            DATABASE,
#            'insert into members (object_id, name, administrator) \
#                values (?, ?, ?)',
#        (member['id'],
#         member['name'],
#         member['administrator']))
