#!/bin/bash

# This script runs the Django and Node.js servers whenver the virtual machine starts.

supervisorctl restart director
supervisorctl restart directornode
