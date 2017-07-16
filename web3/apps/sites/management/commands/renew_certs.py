# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from web3.apps.sites.models import Domain
from web3.apps.sites.helpers import reload_services, generate_ssl_certificate


class Command(BaseCommand):
    help = "Renew all LetsEncrypt certificates"

    def handle(self, **options):
        for domain in Domain.objects.all():
            if domain.has_cert:
                generate_ssl_certificate(domain)
                self.stdout.write("Finished {}".format(domain.domain))
        reload_services()
