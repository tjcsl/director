# -*- coding: utf-8 -*-

import glob
import os
import time

from django.core.management.base import BaseCommand

from web3.apps.sites.models import Site
from web3.apps.sites.helpers import make_site_dirs, fix_permissions, update_supervisor, create_config_files


class Command(BaseCommand):
    help = "Do migration stuff"

    def handle(self, **options):
        for site in Site.objects.all():
            self.stdout.write("Starting {}".format(site.name))

            make_site_dirs(site)
            fix_permissions(site)

            self.stdout.write("Moving log files for {}".format(site.name))

            for fpath in glob.glob(os.path.join(site.private_path, "log-*")):
                if not os.path.islink(fpath):
                    fname = os.path.basename(fpath)
                    os.rename(fpath, os.path.join(site.logs_path, fname))

            compat_symlink_path = os.path.join(site.private_path, "log-" + site.name + ".log")
            if not os.path.exists(compat_symlink_path) and not os.path.islink(compat_symlink_path):
                os.symlink(os.path.join(site.logs_path, "log-" + site.name + ".log"), compat_symlink_path)

            fix_permissions(site)

            if site.category == "dynamic":
                self.stdout.write("Regenerating configuration for {}".format(site.name))

                create_config_files(site)
                self.stdout.write(str(update_supervisor()))

            self.stdout.write("Finished {}".format(site.name))

            time.sleep(5)
