import os
import json

from flask import Flask

APP = Flask(__name__)

@APP.route("/")
def hello():
    return "Hello World!"

@APP.route("/services")
def services():
    return json.dumps(SERVICES, sort_keys=True, indent=4)

def get_env_config(key, default_val=None, val_type=lambda x: x):
    if key not in os.environ:
        return default_val
    return val_type(os.environ[key])

if __name__ == "__main__":
    HOST = get_env_config('VCAP_APP_HOST')
    PORT = get_env_config('PORT', val_type=int)
    SERVICES = get_env_config('VCAP_SERVICES', val_type=json.loads, default_val={})
    DEBUG = get_env_config('APP_DEBUG', default_val=False, val_type=bool)

    APP.run(host=HOST, port=PORT, debug=DEBUG)
