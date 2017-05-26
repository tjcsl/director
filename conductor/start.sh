#!/bin/bash

cd `dirname $0`
gunicorn -w 8 -b 127.0.0.1:4998 agent:app
