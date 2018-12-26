# Director LXC VM architecture

 - Director talks to a libvirt backend, be it LXC or QEMU (I'm focusing on LXC first)
    - Uses ssh as a tunnel protocol, so Director needs passwordless SSH access to any servers where it runs VMs
    - Host object in database contains URL
 - VMs are created on libvirt with the name {hostname}-{uuid}
 - Hostname is the same as name
 - IP: Probably give it an internal IPv4, routed through LXC host.  Probably ephemeral as well?
 - Static IPv6 is fine
 - Template model as well



TODO: 
- [x] list
- [x] console
    - [x] SSH terminal
    - [ ] serial terminal (for recovery)
- [ ] create
    - [ ] generate + copy SSH key
       - SSH keys stored in ~/vm_ssh_keys/uuid{,.pub}
       - `ssh-keygen -N '' -f ~/vm_ssh_keys/<uuid>`
       - enable ssh
    - [ ] add VM to DHCP
    - [ ] add VM to DNS
- [x] delete
    - [ ] have it delete the actual files upon destruction
    - [ ] remove VM from DNS
- [x] info
   - [x] status
   - [x] pause/resume
- [ ] ip addrs
   - ip addrs are going to need DHCP server :(
