from agent import rpc

import dns.query
import dns.tsigkeyring
import dns.update
import sys

keyring = dns.tsigkeyring.from_text({
    'vm.sites.tjhsst.edu.': open("/root/dns.key", "r").read().strip()
})

@rpc.method("dns.add")
def add_dns(host, ip):
    update = dns.update.Update('vm.sites.tjhsst.edu', keyring=keyring)
    update.add(host, 86400, 'AAAA', ip)
    response = dns.query.tcp(update, 'deneb.csl.tjhsst.edu')


@rpc.method("dns.remove")
def remove_dns(host):
    update = dns.update.Update('vm.sites.tjhsst.edu', keyring=keyring)
    update.delete(host)
    response = dns.query.tcp(update, 'deneb.csl.tjhsst.edu')
