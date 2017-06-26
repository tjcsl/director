#!/bin/bash

# This script installs conductor on the machine.
# You will need to run this script in order to use virtual machines.

set -e

export DEBIAN_FRONTEND=noninteractive

if [ "$EUID" -ne 0 ]
then
    echo "You must run the install script as root!"
    exit
fi

cd director/

# Install conductor-agent dependencies
apt-get install -y lxc
pip3 install -U pip
pip3 install -U Flask gunicorn dnspython

# Set up Debian virtual machine template
mkdir -p /var/conductor/debian/rootfs/
mkdir -p /usr/local/var/lib/lxc/
cp conductor/vm_config /var/conductor/debian/config
cp conductor/vm_create /var/conductor/debian/create

# Install Debian on the rootfs
if [ -z "$(ls -A /var/conductor/debian/rootfs)" ]; then
    debootstrap --include=openssh-server stable /var/conductor/debian/rootfs https://deb.debian.org/debian/
fi

supervisorctl start conductoragent
