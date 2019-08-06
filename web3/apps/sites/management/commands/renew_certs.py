# -*- coding: utf-8 -*-

from web3.apps.sites.helpers import generate_ssl_certificate, reload_services
from web3.apps.sites.models import Domain

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Renew all LetsEncrypt certificates"

    def handle(self, **options):
        for domain in Domain.objects.all():
            if domain.has_cert:
                generate_ssl_certificate(domain, renew=True)
                self.stdout.write("Finished {}".format(domain.domain))
        reload_services()
