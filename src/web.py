import os
import datetime
import socket
import functools 
import random
import uuid

import pytz
import postgresql
from flask import Flask, request, json, Response, redirect
from flask_table import Table, Col

MAX_DEPTH = 10
MIME_JSON = 'application/json'

SERVICES = {}
DB_URI = None

APP = Flask(__name__)

class LogTable(Table):
    time = Col('Time')
    src = Col('Source')
    dst = Col('Destination')
    http_method = Col('Method')
    http_path = Col('Path')
    user_agent = Col('User Agent')

class Log:
    def __init__(self, time, src_ip, src_port, dst_ip, dst_port, 
            http_method, http_path, user_agent):
        self.time = time
        self.src = '{0}:{1}'.format(src_ip, src_port)
        self.dst = '{0}:{1}'.format(dst_ip, dst_port)
        self.http_method = http_method
        self.http_path = http_path
        self.user_agent = user_agent

def now():
    return datetime.datetime.utcnow().replace(tzinfo = pytz.utc)

def log_access(f):

    @functools.wraps(f)
    def w(*a, **kw):
        db = connect_db()

        if db is not None:
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
    return 'You are done'

@APP.route('/logs')
@log_access
def logs():
    db = connect_db()

    ps = db.prepare("""
        SELECT * 
        FROM
            (SELECT time, src_ip, src_port, dst_ip, dst_port, 
                http_method, http_path, user_agent
            FROM pyapp_log
            ORDER BY time DESC
            LIMIT 100) AS a
        ORDER BY time ASC
    """)

    return LogTable(Log(*x) for x in ps).__html__()

@APP.route('/env')
@log_access
def dump_services():
    env = {
            'VCAP_SERVICES': SERVICES,
            'APP_DEBUG': DEBUG,
            'VCAP_APP_HOST': HOST,
            'PORT': PORT
            }
    return Response(json.dumps(env, sort_keys=True, indent=4), mimetype='application/json')


def get_env_config(key, default_val=None, val_type=lambda x: x):
    if key not in os.environ:
        return default_val
    return val_type(os.environ[key])

def read_db_info():
    global DB_URI

    if DB_URI is None:
        for k in SERVICES:
            if k.startswith('postgresql'):
                try:
                    uri = SERVICES[k][0]['credentials']['uri']
                except (KeyError, IndexError):
                    continue

                if uri.startswith('postgres://'):
                    DB_URI = uri.replace('postgres://', 'pq://')
                    return

def connect_db():
    if DB_URI is not None:
        return postgresql.open(DB_URI)

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
            db.execute("""CREATE INDEX pyapp_log_time_idx ON pyapp_log (time DESC)""")
    else:
        print('DB schema is up to date')
        


if __name__ == "__main__":
    SERVICES = get_env_config('VCAP_SERVICES', val_type=json.loads, default_val={})
    HOST = get_env_config('VCAP_APP_HOST')
    PORT = get_env_config('PORT', val_type=int)
    DEBUG = get_env_config('APP_DEBUG', default_val=False, val_type=bool)

    read_db_info()
    init_database()

    APP.run(host=HOST, port=PORT, debug=DEBUG)
