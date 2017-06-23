# Director

[![Build Status](https://travis-ci.org/tjcsl/director.svg?branch=master)](https://travis-ci.org/tjcsl/director)

Director (web3) is a website management platform for [TJHSST](https://www.tjhsst.edu/).

## Developing for Director

Before starting development for Director, obtain Ion OAuth credentials from the current maintainer(s).
Clone this repository, and copy `config/devconfig.json.sample` to `config/devconfig.json`.
Edit the `devconfig.json` file and fill out the `ion_key` and `ion_secret` fields.

To develop for Director, you will need to download [Vagrant](https://www.vagrantup.com/downloads.html).
After it is downloaded, you can run `vagrant up` in the folder with the `Vagrantfile`.
This will create a virtual machine to run the Director development environment.
After provisioning is finished, you should be able to access Director at `localhost:8000`.

To stop the virtual machine, you can use the `vagrant halt` command.
You can also suspend and resume the machine using the commands `vagrant suspend` and `vagrant resume`.
You can SSH into the virtual machine using the command `vagrant ssh`.
You can restart the server using the commands `supervisorctl restart director` or `supervisorctl restart directornode`.

Current Director maintainer: [Eric Wang](https://github.com/ezwang) (TJ 2017)
