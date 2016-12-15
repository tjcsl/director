#!/bin/bash

echo $2
sshpass -p '$2' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null root@$1
