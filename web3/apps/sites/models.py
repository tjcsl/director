from __future__ import unicode_literals

import os
import re

from django.conf import settings
from django.db import models

from ..users.models import User, Group


class SiteHost(models.Model):
    """Represents a Director instance.

    Attributes:
        hostname
            The hostname of the Director instance.
    """
    hostname = models.CharField(max_length=255)


class Site(models.Model):

    """Represents a website.

    Attributes:
        name
            The name of the website, max length 32 characters.
        host
            The Director instance that this site is running on.
        category
            What the website runs in the backend.
            If set to static, the webserver will serve static files in the public folder.
            If set to PHP, the website will serve static files in the public folder and execute any php files.
            If set to dynamic, the user will have to select a process to run for the webserver.
            If set to virtual machine, the site will forward to port 80 of a virtual machine that the user selects.
        purpose
            What the website is intended to be used for. This affects the domain that the website uses and
            where the website files are stored.
        description
            A description of the website. For user websites, this is often just the full name of the user.
            For activity websites, this is often the name of the activity.
        user
            The user that processes associated with the website will run as.
        description
            The group that processes associated with the website will run as.
        custom_nginx
            If True, the Nginx configuration will not be automatically generated or overwritten.
        repo_path
            The path of the GitHub repository used for webhooks relative to site.path.
    """
    name = models.CharField(max_length=32, unique=True)
    host = models.ForeignKey(SiteHost, on_delete=models.PROTECT)
    category = models.CharField(max_length=16, choices=(
        ("static", "Static"),
        ("php", "PHP"),
        ("dynamic", "Dynamic"),
        ("vm", "Virtual Machine")
    ))
    purpose = models.CharField(max_length=16, choices=(
        ("legacy", "Legacy"),
        ("user", "User"),
        ("project", "Project"),
        ("activity", "Activity"),
        ("other", "Other")
    ))
    description = models.TextField(blank=True)

    user = models.OneToOneField(User)
    group = models.OneToOneField(Group)

    custom_nginx = models.BooleanField(default=False)
    repo_path = models.TextField(blank=True, null=True, default=None)

    @property
    def path(self):
        if self.purpose == "user":
            return os.path.join(settings.WEB_ROOT, "user", self.name)
        elif self.purpose == "activity":
            return os.path.join(settings.WEB_ROOT, "activities", self.name)
        elif self.purpose == "legacy":
            return os.path.join(settings.WEB_ROOT, "legacy", self.name)
        elif self.purpose == "project":
            return os.path.join(settings.WEB_ROOT, "projects", self.name)
        else:
            return os.path.join(settings.WEB_ROOT, self.name)

    @property
    def url(self):
        if self.purpose == "user":
            return "https://user.tjhsst.edu/{}/".format(self.name)
        elif self.purpose == "activity":
            different_url = self.domain_set.filter(domain__endswith=".sites.tjhsst.edu").first()
            if different_url:
                return "https://activities.tjhsst.edu/{}/".format(different_url.domain.split(".", 1)[0])
            return "https://activities.tjhsst.edu/{}/".format(self.name)
        elif self.purpose == "legacy":
            return "https://www.tjhsst.edu/~{}/".format(self.name)
        else:
            d = self.domain_set.first()
            if not d:
                return None
            return ("https://" if not d.custom_ssl or d.has_cert else "http://") + d.domain

    @property
    def private_path(self):
        return os.path.join(self.path, "private")

    @property
    def public_path(self):
        return os.path.join(self.path, "public")

    @property
    def git_path(self):
        if not self.repo_path:
            return self.public_path
        return os.path.join(self.path, self.repo_path)

    @property
    def has_repo(self):
        if hasattr(self, "_has_repo"):
            return self._has_repo
        self._has_repo = os.path.isdir(os.path.join(self.git_path, ".git"))
        return self._has_repo

    @property
    def public_key(self):
        with open(os.path.join(self.private_path, ".ssh/id_rsa.pub"), "r") as f:
            data = f.read()
        return data

    @property
    def has_rsa_key(self):
        if hasattr(self, "_has_rsa_key"):
            return self._has_rsa_key
        self._has_rsa_key = os.path.isfile(os.path.join(self.private_path, ".ssh/id_rsa"))
        return self._has_rsa_key

    @property
    def has_vm(self):
        return hasattr(self, "virtual_machine")

    @property
    def custom_domains(self):
        return [domain for domain in self.domain_set.all() if domain.custom_ssl]

    @property
    def supports_ssl(self):
        if hasattr(self, "_supports_ssl"):
            return self._supports_ssl
        self._supports_ssl = len([domain for domain in self.domain_set.all() if domain.has_cert]) > 0
        return self._supports_ssl

    def __str__(self):
        return self.name


class Domain(models.Model):
    """Represents a domain.

    Attributes:
        site
            The site that the domain is associated with.
        domain
            The domain as a string.
    """
    site = models.ForeignKey(Site, null=True, on_delete=models.CASCADE)
    domain = models.CharField(max_length=255, unique=True)

    @property
    def custom_ssl(self):
        return not re.match(r"^[a-zA-Z0-9-]+\.tjhsst\.edu", self.domain)

    @property
    def has_cert(self):
        if self.domain.endswith(".sites.tjhsst.edu"):
            return None
        return os.path.isfile("/etc/letsencrypt/live/{}/cert.pem".format(self.domain))

    def __str__(self):
        return self.domain


class Process(models.Model):
    """Represents a process associated with dynamic websites.

    Attributes:
        site
            The site that this process is associated with.
        path
            The absolute path of the script file to run.
    """
    site = models.OneToOneField(Site)
    path = models.FilePathField(path=settings.WEB_ROOT)

    def __str__(self):
        try:
            return self.site.name
        except Exception:
            return "Unknown Site"


class DatabaseHost(models.Model):
    """Represents a host for a collection of SQL databases.

    Attributes:
        hostname
            The host to connect to (ex: postgres1.csl.tjhsst.edu).
        port
            The port the database server is running on.
        username
            The administrator username for creating and managing databases.
        password
            The administrator password for creating and managing databases.
        dbms
            The type of database (ex: postgres, mysql).
    """

    hostname = models.CharField(max_length=255)
    port = models.PositiveIntegerField()
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    dbms = models.CharField(max_length=16, choices=(
        ("postgresql", "PostgreSQL"),
        ("mysql", "MySQL")
    ))

    def __str__(self):
        return "<{}:{}>".format(self.hostname, self.port)


class Database(models.Model):
    """Represents an SQL database that is associated with a website.

    Attributes:
        site
            The site that the database is associated with.
        category
            Whether this database is a MySQL or PostgreSQL database.
        password
            The password of the user used to connect to the database.
            This is automatically generated in most cases.
    """
    site = models.OneToOneField(Site)
    host = models.ForeignKey(DatabaseHost, on_delete=models.CASCADE)
    password = models.CharField(max_length=255)

    @property
    def category(self):
        return self.host.dbms

    @property
    def db_name(self):
        return "site_{}".format(self.site.name).lower()

    @property
    def username(self):
        if self.host.dbms == "mysql":
            return "site_{}".format(self.site.name)[:16].lower()
        return "site_{}".format(self.site.name).lower()

    @property
    def db_host(self):
        return self.host.hostname

    @property
    def db_port(self):
        return self.host.port

    @property
    def db_type(self):
        return "postgres" if self.host.dbms == "postgresql" else "mysql"

    @property
    def db_full_host(self):
        return "{}:{}".format(self.db_host, self.db_port)

    def __str__(self):
        return "{}://{}:{}@{}/{}".format(self.db_type, self.username, self.password, self.db_full_host, self.db_name)
