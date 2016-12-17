import uuid

from django.core.management.base import BaseCommand

from ...models import VirtualMachine
from ...helpers import call_api


class Command(BaseCommand):
    help = "Migrates VMs over from the old Conductor system"

    def handle(self, *args, **options):
        containers = call_api("container.list")
        for container in containers:
            if not VirtualMachine.objects.filter(uuid=container).exists():
                print("[*] Importing {}...".format(container))
                VirtualMachine.objects.create(name=container, uuid=uuid.UUID(container), description="Unknown Virtual Machine")
