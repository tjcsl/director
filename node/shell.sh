#!/bin/bash

export S="$SITE_ROOT"
export HOME="/home/$1"

if [ -z "$2" ]; then
    su - -p -s /bin/bash "$1" -c "$2"
else
    su - -p -s /bin/bash "$1"
fi
