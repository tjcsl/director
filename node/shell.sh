#!/bin/bash

if [ -n "$SITE_ROOT" ];
then
    cd $SITE_ROOT
fi

su - -p -s /bin/bash "$1"
