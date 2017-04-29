# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from web3.apps.sites.models import Site, Domain


class Command(BaseCommand):
    help = "Convert site domains from strings to models"

    def handle(self, **options):
        for site in Site.objects.all():
            site.domain_set.all().delete()
            domains = site.domain_old.strip().split(" ")
            for domain in domains:
                Domain.objects.create(site=site, domain=domain)
            self.stdout.write("Finished {}".format(site.name))
