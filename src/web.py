import os
import datetime
import socket
import functools 
import random
import uuid
import multiprocessing
import queue
import contextlib

import pytz
from flask import Flask, request, json, Response, redirect
from flask_table import Table, Col

import orm

MAX_DEPTH = 10
MIME_JSON = 'application/json'

APP = Flask(__name__)

class LogTable(Table):
    time = Col('Time')
    src = Col('Source')
    dst = Col('Destination')
    http_method = Col('Method')
    http_path = Col('Path')
    user_agent = Col('User Agent')

def now():
    return datetime.datetime.utcnow().replace(tzinfo = pytz.utc)

def log_access(f):

    @functools.wraps(f)
    def w(*a, **kw):
        with orm.session_scope() as session:
                e = request.environ
                
                LOCAL_ADDR = socket.gethostbyname(e['HTTP_HOST'].replace(':%s' % e['SERVER_PORT'], ''))

                method = getattr(orm.HttpMethods, request.method)

                log = orm.PyAppLog(now(), e['REMOTE_ADDR'], int(e['REMOTE_PORT']), 
                        LOCAL_ADDR, int(e['SERVER_PORT']), method, e['PATH_INFO'], e['QUERY_STRING'], 
                        e['HTTP_USER_AGENT'])

                session.add(log)

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
    with orm.session_scope() as session:
        logs = session.query(orm.PyAppLog).order_by(orm.PyAppLog.time.desc()).limit(100).all()
        logs.reverse()
        return LogTable(logs).__html__()

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

def init_database():
    engine = orm.get_engine(SERVICES)
    orm.init_database(engine) 

if __name__ == "__main__":
    print('request-logger startup')

    from cf import HOST, PORT, DEBUG, SERVICES
    
    init_database()

    print('start web app')
    APP.run(host=HOST, port=PORT, debug=DEBUG)
