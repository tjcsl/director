#!/bin/bash

if ! type "lxc" > /dev/null; then
    echo "LXC is not installed, aborting server run..."
    exit 1
fi

cd `dirname $0`
gunicorn -w 8 -b 127.0.0.1:4998 agent:app
