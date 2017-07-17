#!/bin/bash

export S="$SITE_ROOT"
export HOME="/home/$1"

su - -p -s /bin/bash "$1"
