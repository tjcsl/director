#!/bin/bash

# This script runs the Django, Node.js, and conductor-agent servers whenver the virtual machine starts.

export DEBIAN_FRONTEND=noninteractive

supervisorctl start director
supervisorctl start directornode
supervisorctl start conductoragent
