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
            '2016fwilson': 'user',
            '2017awang': 'user',
            '2017jchen': 'user',
            '2017jstone': 'user',
            '2018nthistle': 'user',
            'crs': 'activity',
            'homecoming': 'other',
            'quizbowl': 'activity',
            'techstrav': 'activity',
            'tmrudwick': 'user',
            '2016jwoglom': 'user',
            '2017blyons': 'user',
            '2017jhoughto': 'user',
            '2017lwang': 'user',
            '2018wzhang': 'user',
            'botball': 'activity',
            'csc': 'activity',
            'mun': 'activity',
            'sct': 'activity',
            'teknos': 'activity',
            'tutoring': 'other',
            'vmt': 'activity',
            '2017asumesh': 'user',
            '2017jschefer': 'user',
            '2017sdamashe': 'user',
            'chemteam': 'activity',
            'ghs': 'activity',
            'nhs': 'activity',
            'smtorbert': 'user',
            'tjstar': 'activity',
            'twist': 'activity'
        }
        for name in mappings:
            s = Site(name=name, domain="{}.sites.tjhsst.edu".format(name), category="php", purpose=mappings[name])
            create_site_users(s)
            make_site_dirs(s)
            create_config_files(s)
            shutil.copytree("/web_old/{}/public/".format(s.name), "{}public".format(s.path))
            os.system("chown -R {}:{} {}".format(s.user.username, s.group.name, s.path))
            self.stdout.write("Created Site: {}".format(s))
        reload_services()
