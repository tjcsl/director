# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.require_version ">= 1.8.4"

require "json"
require "time"

devconfig = JSON.parse(File.read("config/devconfig.json"))

VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "ubuntu/xenial64"
  config.vm.boot_timeout = 1000
  config.vm.network "public_network", bridge: devconfig["network_interface"]
  config.vm.network "forwarded_port", guest: 8000, host: 8000

  config.ssh.forward_agent = true

  config.vm.hostname = "directorvm"

  config.vm.define "director-vagrant" do |v|
  end

  config.vm.provider :virtualbox do |vb|
    vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
    vb.customize ["modifyvm", :id, "--natdnsproxy1", "on"]
    vb.customize ["modifyvm", :id, "--nictype1", "virtio"]
    vb.name = "director-vagrant"
    vb.memory = 1024 # the default of 512 gives us a OOM during setup.
    # vb.gui = true
  end

  config.vm.synced_folder ".", "/vagrant", disabled: true
  config.vm.synced_folder ".", "/home/ubuntu/director"

  config.vm.provision "file",
    source: "~/.ssh/#{devconfig['ssh_key']}",
    destination: ".ssh/#{devconfig['ssh_key']}"

  config.vm.provision "file",
    source: "~/.ssh/#{devconfig['ssh_key']}.pub",
    destination: ".ssh/#{devconfig['ssh_key']}.pub"

  config.vm.provision "shell", path: "config/provision_vagrant.sh"
  config.vm.provision "shell", path: "config/run_vagrant.sh", run: "always"
end
