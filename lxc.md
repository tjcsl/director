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
- [-] console
    - [x] SSH terminal
    - [ ] serial terminal (for recovery)
- [-] create
    - [x] copy template
    - [x] define domain
    - [x] change MAC address
    - [x] generate + copy SSH key
       - SSH keys stored in /home/<owner>/.ssh/uuid{,.pub}
       - `ssh-keygen -N '' -f /home/<owner>/.ssh/<uuid>`
       - enable ssh
    - [ ] notify user of completion once it is complete
    - [x] add VM to DHCP
    - [ ] add VM to DNS
- [-] delete
    - [x] have it delete the actual files upon destruction
    - [x] remove VM from DHCP
    - [ ] remove VM from DNS
- [x] info
   - [x] status
   - [x] pause/resume
- [x] ip addrs
   - ip addrs are going to need DHCP server :(
