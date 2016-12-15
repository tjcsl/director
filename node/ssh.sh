#!/bin/bash

ssh -p '$2' -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null root@$1
