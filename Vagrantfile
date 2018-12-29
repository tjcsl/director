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
  # config.vm.network "public_network", bridge: devconfig["network_interface"]
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
  config.vm.provider :libvirt do |libvirt|
      libvirt.cpus = 4
      libvirt.memory = 1024
  end
  config.bindfs.default_options = {
    force_user:   'vagrant',
    force_group:  'vagrant',
    perms:        'u=rwX:g=rD:o=rD'
  }
  config.vm.network :private_network, ip: '192.168.50.50'
  config.vm.synced_folder ".", "/vagrant", disabled: true
  config.nfs.map_uid = Process.uid
  config.nfs.map_gid = Process.gid
  config.vm.synced_folder "../director", "/vagrant-nfs", type: :nfs, nfs_udp: false
  config.bindfs.bind_folder "/vagrant-nfs", "/home/vagrant/director",
    force_user: 'vagrant',
    force_group: 'vagrant'

  RSA_PUB = File.join(ENV["HOME"], ".ssh/id_rsa.pub")
  RSA_PRIV = File.join(ENV["HOME"], ".ssh/id_rsa")
  GIT_CONF = File.join(ENV["HOME"], ".gitconfig")

  if File.file?(RSA_PUB)
    config.vm.provision "file",
      source: RSA_PUB,
      destination: ".ssh/id_rsa.pub"
  end

  if File.file?(RSA_PRIV)
    config.vm.provision "file",
      source: RSA_PRIV,
      destination: ".ssh/id_rsa"
  end

  if File.file?(GIT_CONF)
    config.vm.provision "file",
      source: GIT_CONF,
      destination: ".gitconfig"
  end

  config.vm.provision "shell", path: "config/provision_vagrant.sh"
  config.vm.provision "shell", path: "config/run_vagrant.sh", run: "always"
end
