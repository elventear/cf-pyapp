import os

import postgresql
from flask import Flask, request, json, Response

MIME_JSON = 'application/json'

SERVICES = {}

APP = Flask(__name__)

@APP.route("/")
def hello():
    return "Hello World!"

@APP.route("/services")
def services():
    return Response(json.dumps(SERVICES, sort_keys=True, indent=4), 
            mimetype=MIME_JSON)

@APP.route("/headers")
def headers():
    return Response(json.dumps(dict(request.headers), sort_keys=True, indent=4), 
            mimetype=MIME_JSON)

@APP.route("/request")
def request_():
    return request.remote_ip

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
        return

    if tables_missing(db):
        print('Creating DB schema')
        db.execute("""CREATE TYPE http_method AS ENUM (
                'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'TRACE', 'CONNECT')""")
        db.execute("""
            CREATE TABLE pyapp_log (
                id integer  PRIMARY KEY,
                time timestamptz NOT NULL,
                src_ip inet NOT NULL ,
                src_post integer NOT NULL,
                dst_ip inet NOT NULL,
                dst_port integer NOT NULL,
                http_method http_method NOT NULL,
                http_path text NOT NULL
            )
        """)
        


if __name__ == "__main__":
    SERVICES = get_env_config('VCAP_SERVICES', val_type=json.loads, default_val={})

    init_database()

    APP.run(host=get_env_config('VCAP_APP_HOST'), port=get_env_config('PORT', val_type=int), 
            debug=get_env_config('APP_DEBUG', default_val=False, val_type=bool))
