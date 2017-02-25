#!/bin/bash

# This script is intended for setting up a development environment.
# Additional configuration is necessary for production.

set -e

if [ "$EUID" -ne 0 ]
then
    echo "You must run the install script as root!"
    exit
fi

DB_PASS='web3'

apt-get update
apt-get upgrade -y

apt-get install -y sudo python3 python3-dev python3-pip virtualenv libnss-pgsql2 nodejs supervisor
apt-get install -y postgresql postgresql-contrib libpq-dev libmysqlclient-dev

cp web3/settings/secret.sample web3/settings/secret.py

# Set the database password
sed -i 's/^DB_PASSWORD.*/DB_PASSWORD = "'"$DB_PASS"'"/' web3/settings/secret.py

# Turn off DEBUG to use the postgresql database
sed -i 's/^DEBUG.*/DEBUG = False/' web3/settings/secret.py

# Remove Raven logging
sed -i '/dsn/d' web3/settings/secret.py

# Create web3 user and database
sudo -u postgres createuser -D -A "web3"
sudo -u postgres psql -c "ALTER USER web3 WITH PASSWORD '$DB_PASS';"
sudo -u postgres createdb -O "web3" "web3"

mkdir /web

virtualenv --python python3 venv
source venv/bin/activate
pip install -U -r requirements.txt

./manage.py migrate

# Set up nss-pgsql
apt-get -y install nscd
cp conf/nss-pgsql.conf /etc/nss-pgsql.conf
chmod 644 /etc/nss-pgsql.conf
sed -i 's/^connectionstring.*/connectionstring = hostaddr=127.0.0.1 dbname=web3 user=web3 password='"$DB_PASS"' connect_timeout=1/' /etc/nss-pgsql.conf
sed -i 's/^passwd:.*/passwd: compat pgsql/' /etc/nsswitch.conf
sed -i 's/^group:.*/group: compat pgsql/' /etc/nsswitch.conf
/usr/sbin/nscd -i group
/usr/sbin/nscd -i passwd
