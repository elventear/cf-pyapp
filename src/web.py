import os
import datetime
import socket
import functools 
import random
import uuid

import pytz
import postgresql
from flask import Flask, request, json, Response, redirect

MAX_DEPTH = 10
MIME_JSON = 'application/json'

SERVICES = {}

APP = Flask(__name__)

def now():
    return datetime.datetime.utcnow().replace(tzinfo = pytz.utc)

def log_access(f):

    @functools.wraps(f)
    def w(*a, **kw):
        db = connect_db()

        e = request.environ
        
        LOCAL_ADDR = socket.gethostbyname(e['HTTP_HOST'].replace(':%s' % e['SERVER_PORT'], ''))

        db.query("""
            INSERT INTO pyapp_log(time, src_ip, src_port, dst_ip, dst_port, 
                http_method, http_path, http_query, user_agent) 
            VALUES ($1, ($2 || '/32')::inet, $3, ($4 || '/32')::inet, $5, $6, $7, $8, $9)
        """, now(), e['REMOTE_ADDR'], int(e['REMOTE_PORT']), LOCAL_ADDR, 
            int(e['SERVER_PORT']), request.method, e['PATH_INFO'], e['QUERY_STRING'], e['HTTP_USER_AGENT']
        )
        
        return f(*a, **kw)

    return w


@APP.route('/', methods=['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'TRACE', 'CONNECT'], defaults={'path': ''})
@APP.route('/<path:path>', methods=['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'TRACE', 'CONNECT'])
@log_access
def loop(path):
    if len(path.split('/')) >= MAX_DEPTH:
        return redirect('/end', code=302) 
    level = ''.join(random.SystemRandom().sample(uuid.uuid4().hex, 10))
    next_level = '/'.join([path, level])
    return redirect(next_level, code=302)

@APP.route('/end', methods=['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'TRACE', 'CONNECT'])
@log_access
def end():
    return 'a'

def get_env_config(key, default_val=None, val_type=lambda x: x):
    if key not in os.environ:
        return default_val
    return val_type(os.environ[key])

def connect_db():
    try:
        uri = SERVICES['database'][0]['credentials']['uri']
    except (KeyError, IndexError):
        return None

    if uri.startswith('postgres://'):
        uri = uri.replace('postgres://', 'pq://')
        return postgresql.open(uri)


def tables_missing(db):
    return db.query("SELECT count(*) FROM information_schema.tables WHERE table_name = 'pyapp_log'",)[0][0] == 0

def init_database():
    db = connect_db()

    if db is None:
        print('Database is not found')
        return

    if tables_missing(db):
        print('Creating DB schema')
        with db.xact():
            db.execute("""CREATE TYPE http_method AS ENUM (
                    'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'TRACE', 'CONNECT')""")
            db.execute("""
                CREATE TABLE pyapp_log (
                    id SERIAL PRIMARY KEY,
                    time timestamptz NOT NULL,
                    src_ip inet NOT NULL ,
                    src_port integer NOT NULL,
                    dst_ip inet NOT NULL,
                    dst_port integer NOT NULL,
                    http_method http_method NOT NULL,
                    http_path text NOT NULL,
                    http_query text NOT NULL,
                    user_agent text NOT NULL
                )
            """)
    else:
        print('DB schema is up to date')
        


if __name__ == "__main__":
    SERVICES = get_env_config('VCAP_SERVICES', val_type=json.loads, default_val={})

    init_database()

    APP.run(host=get_env_config('VCAP_APP_HOST'), port=get_env_config('PORT', val_type=int), 
            debug=get_env_config('APP_DEBUG', default_val=False, val_type=bool))
