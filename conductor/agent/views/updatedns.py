from agent import rpc
from ipaddress import ip_address

import dns.query
import dns.tsigkeyring
import dns.update

DNS_DOMAIN = 'vm.sites.tjhsst.edu'
DNS_SERVER = 'deneb.csl.tjhsst.edu'
DNS_KEY = {}
DNS_KEY['{}.'.format(DNS_DOMAIN)] = open("/root/dns.key", "r").read().strip()

keyring = dns.tsigkeyring.from_text(DNS_KEY)


@rpc.method("dns.add")
def add_dns(host, ip):
    if not ip:
        return
    update = dns.update.Update(DNS_DOMAIN, keyring=keyring)
    if ip_address(ip).version == 6:
        update.add(host, 86400, 'AAAA', ip)
    else:
        update.add(host, 86400, 'A', ip)
    dns.query.tcp(update, DNS_SERVER)


@rpc.method("dns.remove")
def remove_dns(host):
    update = dns.update.Update(DNS_DOMAIN, keyring=keyring)
    update.delete(host)
    dns.query.tcp(update, DNS_SERVER)
