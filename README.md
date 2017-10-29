# Director [![Build Status](https://travis-ci.org/tjcsl/director.svg?branch=master)](https://travis-ci.org/tjcsl/director)

[![Join the chat at https://gitter.im/tjcsl/director](https://badges.gitter.im/tjcsl/director.svg)](https://gitter.im/tjcsl/director?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

Director (web3) is a website management platform for [TJHSST](https://www.tjhsst.edu/).

## Developing for Director

Before starting development for Director, generate Ion OAuth credentials [here](https://ion.tjhsst.edu/oauth/applications/).
Clone this repository, and copy `config/devconfig.json.sample` to `config/devconfig.json`.
Edit the `devconfig.json` file and fill out the `ion_key` and `ion_secret` fields with your Ion OAuth credentials.

To develop for Director, you will need to download [Vagrant](https://www.vagrantup.com/downloads.html).
After it is downloaded, you can run `vagrant up` in the folder with the `Vagrantfile`.
This will create a virtual machine to run the Director development environment.
After provisioning is finished, you should be able to access Director at `localhost:8000`.

To stop the virtual machine, you can use the `vagrant halt` command.
You can also suspend and resume the machine using the commands `vagrant suspend` and `vagrant resume`.
You can SSH into the virtual machine using the command `vagrant ssh`.
You can restart the server using the commands `supervisorctl restart director` or `supervisorctl restart directornode`.

The Conductor agent is not installed by default. To install the Conductor agent, SSH into the machine and run `sudo bash director/config/provision_conductor.sh`.

Current Director maintainer: [Naitian Zhou](https://github.com/naitian) (TJ 2018)
