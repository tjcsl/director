#!/bin/bash

if [ -n "$SITE_ROOT" ];
then
    cd $SITE_ROOT

    function cd() {
        NEW_DIR="$*"
        if [ $# -eq 0 ] || [ "$NEW_DIR" == "$HOME" ];
        then
            NEW_DIR="$SITE_ROOT"
        fi
        builtin cd "${NEW_DIR}"
    }
    export -f cd
fi

export HOME="/home/$1/"

su - -p -s /bin/bash "$1"
