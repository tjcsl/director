from __future__ import unicode_literals

from django.apps import AppConfig


class SitesConfig(AppConfig):
    name = "sites"

    def ready(self):
        import web3.apps.sites.signals  # noqa
