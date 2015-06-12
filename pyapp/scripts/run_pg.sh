#!/bin/bash 

set -e  

DBUSER=pyapp
DBUSERPW=$DBUSER
DBNAME=$DBUSER

ROOT=$(dirname $0)
DATA=$ROOT/../tmp/data
PGLOG=$DATA/pg.log

if [ ! -d $DATA ]; then
    pg_ctl init -D $DATA -s -o "--auth-host md5" > /dev/null 2>&1
    NEWINIT=1
fi

pg_ctl status -D $DATA > /dev/null || pg_ctl start -w -D $DATA -l $PGLOG -s 

if [ ! -z $NEWINIT ]; then
    createuser $DBUSER
    echo "ALTER ROLE $DBUSER with PASSWORD '$DBUSERPW'" | psql postgres > /dev/null
    createdb -O $DBUSER $DBNAME
fi

echo "VCAP_SERVICES='{\"database\": [{\"name\": \"myinstance\",\"credentials\": {\"uri\": \"postgres://$DBUSER:$DBNAME@localhost:5432/$DBNAME\"}}]}'; export VCAP_SERVICES"
