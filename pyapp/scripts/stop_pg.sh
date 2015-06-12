#!/bin/bash 

set -e 

ROOT=$(dirname $0)
DATA=$ROOT/../tmp/data

test -d $DATA && { pg_ctl status -D $DATA > /dev/null && pg_ctl stop -D $DATA; }
