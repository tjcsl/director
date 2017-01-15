from agent import rpc
from ipaddress import ip_address

import dns.query
import dns.tsigkeyring
import dns.update

keyring = dns.tsigkeyring.from_text({
    'vm.sites.tjhsst.edu.': open("/root/dns.key", "r").read().strip()
})


@rpc.method("dns.add")
def add_dns(host, ip):
    update = dns.update.Update('vm.sites.tjhsst.edu', keyring=keyring)
    if ip_address(ip).version == 6:
        update.add(host, 86400, 'AAAA', ip)
    else:
        update.add(host, 86400, 'A', ip)
    dns.query.tcp(update, 'deneb.csl.tjhsst.edu')


@rpc.method("dns.remove")
def remove_dns(host):
    update = dns.update.Update('vm.sites.tjhsst.edu', keyring=keyring)
    update.delete(host)
    dns.query.tcp(update, 'deneb.csl.tjhsst.edu')
