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

## Cloud Foundry Deployment

    > cf create-service postgresql default my-postgresql
    > cd src
    > cf push
    > cf bind-service request-logger my-postgresql
    > cf restage request-logger

## Accessing the Application

To log a series of requests:

    > curl -L -X POST http://request-logger.example.domain.com

Any HTTP method is accepted. 

To view the logs visit `http://request-logger.example.domain.com/logs`.

    


