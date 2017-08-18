# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf import settings

from django.db import migrations


def forwards_func(apps, schema_editor):
    DatabaseHost = apps.get_model("sites", "DatabaseHost")
    Database = apps.get_model("sites", "Database")

    mysql, created = DatabaseHost.objects.get_or_create(
        hostname=settings.MYSQL_DB_HOST,
        port=settings.MYSQL_DB_PORT,
        username=settings.MYSQL_DB_USER,
        password=settings.MYSQL_DB_PASS,
        dbms="mysql"
    )

    postgresql, created = DatabaseHost.objects.get_or_create(
        hostname=settings.POSTGRES_DB_HOST,
        port=settings.POSTGRES_DB_PORT,
        username=settings.POSTGRES_DB_USER,
        password=settings.POSTGRES_DB_PASS,
        dbms="postgresql"
    )

    for db in Database.objects.all():
        if db.category == "mysql":
            db.host = mysql
        else:
            db.host = postgresql
        db.save()


def reverse_func(apps, schema_editor):
    Database = apps.get_model("sites", "Database")

    for db in Database.objects.all():
        if db.host.dbms == "mysql":
            db.category = "mysql"
        else:
            db.category = "postgresql"
        db.save()


class Migration(migrations.Migration):
    dependencies = [
        ('sites', '0018_auto_20170818_1148'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func)
    ]
