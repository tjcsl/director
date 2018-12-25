#!/bin/bash
# usage: $0 <ip addr> <vm uuid>

# sshpass -e ssh -o LogLevel=ERROR -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "root@$1"
ssh -i /home/"$3"/.ssh/"$2" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "root@$1"
