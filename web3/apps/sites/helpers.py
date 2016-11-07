import os
import stat
from subprocess import Popen

from ..users.models import User, Group


def create_site_users(site):
    try:
        user = User.objects.get(username="site_{}".format(site.name))
    except User.DoesNotExist:
        user = User.objects.create(id=get_next_id(), service=True, username="site_{}".format(site.name), email="site_{}@tjhsst.edu".format(site.name))
    try:
        group = Group.objects.get(name="site_{}".format(site.name))
    except Group.DoesNotExist:
        group = Group.objects.create(id=user.id, service=True, name="site_{}".format(site.name))
        group.users.add(user)
        group.save()
    return (user, group)


def get_next_id():
    return list(User.objects.filter(service=True).order_by('id'))[-1].id + 1


def make_site_dirs(site):
    for i in ["{}", "{}/public", "{}/private"]:
        os.mkdir(i.format(site.path))
        os.chown(i.format(site.path), site.user.id, site.group.id)
        os.chmod(i.format(site.path), stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
                 | stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP
                 | stat.S_ISGID)
    Popen("/usr/bin/setfacl -Rdm g:{}:rwx {}".format(site.group.name, site.path).split())
