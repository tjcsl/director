# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from web3.apps.sites.models import Site
from web3.apps.sites.helpers import create_site_users, make_site_dirs, create_config_files, reload_services

import shutil
import os


class Command(BaseCommand):
    help = "Import websites from web2 (/web_old)"

    def handle(self, **options):
        mappings = {
        }
        for name in mappings:
            s = Site(name=name, domain="{}.sites.tjhsst.edu".format(
                name), category="php", purpose=mappings[name])
            create_site_users(s)
            make_site_dirs.delay(s.pk)
            create_config_files.delay(s.pk)
            shutil.move("/web_old/{}/public/".format(s.name),
                        "{}public".format(s.path))
            os.system(
                "chown -R {}:{} {}".format(s.user.username, s.group.name, s.path))
            self.stdout.write("Created Site: {}".format(s))
        reload_services()
