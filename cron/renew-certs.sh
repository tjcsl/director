#!/bin/bash

cd /usr/local/www/director
source venv/bin/activate
./manage.py renew_certs
