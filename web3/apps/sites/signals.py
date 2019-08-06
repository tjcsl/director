from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .database_helpers import delete_mysql_database, delete_postgres_database
from .helpers import (delete_process_config, delete_site_files,
                      reload_services, update_supervisor)
from .models import Database, Process, Site


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
