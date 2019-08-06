from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .models import Database, Site, Process

from .helpers import (
    delete_site_files,
    reload_services,
    delete_process_config,
    update_supervisor,
)
from .database_helpers import delete_postgres_database, delete_mysql_database


@receiver(pre_delete, sender=Database, dispatch_uid="database_delete_signal")
def pre_database_delete(sender, instance, using, **kwargs):
    if instance.category == "mysql":
        delete_mysql_database(instance)
    else:
        delete_postgres_database(instance)


@receiver(pre_delete, sender=Site, dispatch_uid="site_delete_signal")
def pre_site_delete(sender, instance, using, **kwargs):
    delete_site_files(instance)
    reload_services(instance)

    instance.user.delete()
    instance.group.delete()


@receiver(pre_delete, sender=Process, dispatch_uid="process_delete_signal")
def pre_process_delete(sender, instance, using, **kwargs):
    delete_process_config(instance)
    update_supervisor()
