#!/bin/bash

# This script is intended for setting up a development environment.
# Additional configuration is necessary for production.

set -e

if [ "$EUID" -ne 0 ]
then
    echo "You must run the install script as root!"
    exit
fi

function devconfig() {
    python3 -c "
import json
with open('/home/ubuntu/director/config/devconfig.json', 'r') as f:
    print(json.load(f)['$1'])"
}

export DEBIAN_FRONTEND=noninteractive

if ! grep -Fxq "openldap1.csl.tjhsst.edu" /etc/hosts
then
    echo 198.38.16.70 openldap1.csl.tjhsst.edu >> /etc/hosts
fi

DB_PASS='web3'

apt-get update
apt-get upgrade -y

apt-get install -y git
apt-get install -y php-fpm

apt-get install -y sudo python python-dev python3 python3-dev python3-pip virtualenv libnss-pgsql2 nodejs nodejs-legacy supervisor
apt-get install -y postgresql postgresql-contrib libpq-dev libmysqlclient-dev nginx

mkdir -p /etc/nginx/director.d/
mkdir -p /etc/supervisor/director.d/
mkdir -p /var/log/gunicorn/

cd director/

cp web3/settings/secret.sample web3/settings/secret.py

cp config/dev-nginx.conf /etc/nginx/nginx.conf
nginx -s reload

# Set the database password
sed -i 's/^DB_PASSWORD.*/DB_PASSWORD = "'"$DB_PASS"'"/' web3/settings/secret.py

# Turn on debug to see more detailed error messages
sed -i 's/^DEBUG.*/DEBUG = True/' web3/settings/secret.py

# Remove Raven logging
sed -i '/dsn/d' web3/settings/secret.py

sed -i 's/^SOCIAL_AUTH_ION_KEY.*/SOCIAL_AUTH_ION_KEY = "'"$(devconfig ion_key)"'"/' web3/settings/secret.py
sed -i 's/^SOCIAL_AUTH_ION_SECRET.*/SOCIAL_AUTH_ION_SECRET = "'"$(devconfig ion_secret)"'"/' web3/settings/secret.py

# Create web3 user and database
sudo -u postgres createuser -D -A "web3" || echo "User already exists"
sudo -u postgres psql -c "ALTER USER web3 WITH PASSWORD '$DB_PASS';"
sudo -u postgres createdb -O "web3" "web3" || echo "Database already exists"

# Create www-data user
useradd www-data || echo "www-data user already exists"

mkdir -p /web

if [ ! -d "venv" ]; then
    virtualenv --python python3 venv
fi
source venv/bin/activate
pip install -U -r requirements.txt

./manage.py migrate

# Set up nss-pgsql
apt-get -y install nscd
cp config/nss-pgsql.conf /etc/nss-pgsql.conf
chmod 644 /etc/nss-pgsql.conf
sed -i 's/^connectionstring.*/connectionstring = hostaddr=127.0.0.1 dbname=web3 user=web3 password='"$DB_PASS"' connect_timeout=1/' /etc/nss-pgsql.conf
sed -i 's/^passwd:.*/passwd: compat pgsql/' /etc/nsswitch.conf
sed -i 's/^group:.*/group: compat pgsql/' /etc/nsswitch.conf
/usr/sbin/nscd -i group
/usr/sbin/nscd -i passwd

cp config/dev-supervisord.conf /etc/supervisor/supervisord.conf
supervisorctl reread
supervisorctl update

# Automatically start supervisor on boot
systemctl enable supervisor

supervisorctl restart director
supervisorctl restart directornode
