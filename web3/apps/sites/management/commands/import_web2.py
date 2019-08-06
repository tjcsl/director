# -*- coding: utf-8 -*-

import os
import shutil

from web3.apps.sites.helpers import (create_config_files, create_site_users,
                                     make_site_dirs, reload_services)
from web3.apps.sites.models import Site

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Import websites from web2 (/web_old)"

    def handle(self, **options):
        mappings = {}
        for name in mappings:
            s = Site(
                name=name,
                domain="{}.sites.tjhsst.edu".format(name),
                category="php",
                purpose=mappings[name],
            )
            create_site_users(s)
            make_site_dirs(s)
            create_config_files(s)
            shutil.move("/web_old/{}/public/".format(s.name), "{}public".format(s.path))
            os.system("chown -R {}:{} {}".format(s.user.username, s.group.name, s.path))
            self.stdout.write("Created Site: {}".format(s))
        reload_services()
