# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from web3.apps.sites.models import Site
from web3.apps.sites.helpers import make_site_dirs, fix_permissions, reload_services, create_config_files


class Command(BaseCommand):
    help = "Rewrite all site configurations and reset all permissions"

    def add_arguments(self, parser):
        parser.add_argument('--no-permissions', action='store_true',
                            dest='noperms', default=False, help="Don't reset permissions.")
        parser.add_argument('--no-config', action='store_true', dest='noconfig',
                            default=False, help="Don't create configuration files.")

    def handle(self, **options):
        for site in Site.objects.all():
            make_site_dirs.delay(site.pk)
            if not options["noperms"]:
                fix_permissions.delay(site)
            if not options["noconfig"]:
                create_config_files.delay(site.pk)
            self.stdout.write("Finished {}".format(site.name))
        reload_services()
