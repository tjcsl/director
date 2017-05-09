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

export HOME="/home/$1"
export PATH="/home/$1/bin:/home/$1/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games"

su - -p -s /bin/bash "$1"
