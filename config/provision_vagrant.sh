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

DB_PASS='web3'
NSS_PASS='web3'

apt-get update
apt-get upgrade -y

apt-get install -y git
apt-get install -y php-fpm

apt-get install -y sudo python python-dev python3 python3-dev python3-pip virtualenv libnss-pgsql2 nodejs nodejs-legacy supervisor
apt-get install -y postgresql postgresql-contrib libpq-dev nginx
apt-get install -y libmysqlclient-dev mysql-client-core-5.7

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

# Setup Ion OAuth
sed -i 's/^SOCIAL_AUTH_ION_KEY.*/SOCIAL_AUTH_ION_KEY = "'"$(devconfig ion_key)"'"/' web3/settings/secret.py
sed -i 's/^SOCIAL_AUTH_ION_SECRET.*/SOCIAL_AUTH_ION_SECRET = "'"$(devconfig ion_secret)"'"/' web3/settings/secret.py

# Create web3 user and database
sudo -u postgres createuser -D -A "web3" || echo "web3 user already exists"
sudo -u postgres psql -c "ALTER USER web3 WITH PASSWORD '$DB_PASS';"
sudo -u postgres createdb -O "web3" "web3" || echo "Database already exists"

# Create nss user and give access
sudo -u postgres createuser -D -A "nss" || echo "nss user already exists"
sudo -u postgres psql -c "ALTER USER nss WITH PASSWORD '$NSS_PASS';"

# Create www-data user
useradd www-data || echo "www-data user already exists"

mkdir -p /web

if [ ! -d "venv" ]; then
    virtualenv --python python3 venv
fi
source venv/bin/activate
pip install -U -r requirements.txt

./manage.py migrate --no-input

# Give nss user specific permissions
sudo -u postgres psql -c "GRANT CONNECT ON DATABASE web3 TO nss;"
sudo -u postgres psql -d "web3" -c "GRANT SELECT (id, username, staff, is_superuser) ON TABLE users_user TO nss;"
sudo -u postgres psql -d "web3" -c "GRANT SELECT ON TABLE users_group TO nss;"
sudo -u postgres psql -d "web3" -c "GRANT SELECT ON TABLE users_group_users TO nss;"
sudo -u postgres psql -d "web3" -c "GRANT SELECT ON TABLE users_user_groups TO nss;"

# Setup nss-pgsql
apt-get -y install nscd
cp config/nss-pgsql.conf /etc/nss-pgsql.conf
chmod 644 /etc/nss-pgsql.conf
sed -i 's/^connectionstring.*/connectionstring = hostaddr=127.0.0.1 dbname=web3 user=nss password='"$NSS_PASS"' connect_timeout=1/' /etc/nss-pgsql.conf
sed -i 's/^passwd:.*/passwd: compat pgsql/' /etc/nsswitch.conf
sed -i 's/^group:.*/group: compat pgsql/' /etc/nsswitch.conf
/usr/sbin/nscd -i group
/usr/sbin/nscd -i passwd

# Setup loggging directory
mkdir -p /var/log/nginx/director/
chmod o-rwx /var/log/nginx/director/

# Make install scripts folder
mkdir -p /scripts/
cp scripts/* /scripts/

# Setup supervisor
cp config/dev-supervisord.conf /etc/supervisor/supervisord.conf
systemctl start supervisor
supervisorctl reread
supervisorctl update

# Automatically start supervisor on boot
systemctl enable supervisor
