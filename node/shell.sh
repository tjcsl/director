#!/bin/bash

if [ -n "$SITE_ROOT" ];
then
    cd $SITE_ROOT
    function cd() {
        new_dir="$*"
        if [ $# -eq 0 ] || [ "$1" == "$HOME" ];
        then
            new_dir="$SITE_ROOT"
        fi
        builtin cd "${new_dir}"
    }
fi

su - -p -s /bin/bash "$1"
