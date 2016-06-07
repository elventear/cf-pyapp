import os
import json

def get_env_config(key, default_val=None, val_type=lambda x: x):
    try:
        val = os.environ[key]
    except KeyError:
        if default_val is None:
            print(key, 'not found in enviroment')
            raise
        val = default_val

    return val_type(val)

SERVICES = get_env_config('VCAP_SERVICES', val_type=json.loads, default_val={})
HOST = get_env_config('VCAP_APP_HOST', default_val='0.0.0.0')
PORT = get_env_config('PORT', val_type=int, default_val=8888)
DEBUG = get_env_config('APP_DEBUG', default_val=False, val_type=lambda x: x == 'true')

