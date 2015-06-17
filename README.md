# cf txn demo app

Simple web app that logs each access to a database

## Features

Vising any path served by the server will trigger a redirect to a new path that is deeper than the original request.
When the path reaches a certain depth (10), it will redirect to `/end` and stop redirecting. Any access to the server
will be saved in a database.

To view the logs visit `/logs`. Only the last 100 accesses will be returned.

## Development

### Requirements

* Python 3.4
* virtualenv
- postgresql

### Init enviroment

    > virtualenv .venv
    > source .env
    > pip install -r src/requirements.txt
    > eval $(./scripts/run_pg.sh)

### Usage

    > python src/web.py


