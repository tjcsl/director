from .models import User, Group
from ..sites.models import Site, SiteHost, Domain
from ..sites.helpers import (
    create_site_users,
    make_site_dirs,
    create_config_files,
    flush_permissions,
    reload_nginx_config,
)
from ...utils.tjldap import get_uid, get_full_name


def generate_debug_id(username):
    """Used in development environments to generate a user id when logging in.
    This avoids having to connect to the LDAP server (which requires VPN externally) in order to get an id.
    """
    if User.objects.filter(username=username).exists():
        return User.objects.get(username=username).id

    if User.objects.filter(service=False).count() == 0:
        return 30000

    return User.objects.filter(service=False).order_by("-id")[0].id + 1


def create_user(request, username):
    if User.objects.filter(username=username).exists():
        return User.objects.get(username=username)

    try:
        uid = get_uid(username)
    except IndexError:
        return None

    profile = request.user.api_request("profile/{}".format(username))

    full_name = profile.get("full_name", get_full_name(username))

    if not full_name:
        return None

    user = User.objects.create(
        id=uid,
        username=username,
        full_name=full_name,
        email=profile.get("tj_email", "{}@tjhsst.edu".format(username)),
        staff=profile.get("is_teacher", False),
        is_superuser=profile.get("is_eighth_admin", False),
    )

    if not Group.objects.filter(id=user.id).exists():
        group = Group.objects.create(id=user.id, service=False, name=user.username)
        group.users.add(user.pk)
        group.save()

    Group.objects.get(id=1337).users.add(user.pk)

    return user


def create_webdocs(user, batch=False, purpose="user"):
    if isinstance(user, str):
        username = user
        full_name = user
    else:
        username = user.username
        full_name = user.full_name

    if Site.objects.filter(name=username).exists():
        return Site.objects.get(name=username)

    site = Site(
        name=username,
        host=SiteHost.objects.first(),
        description=full_name,
        category="php",
        purpose=purpose,
        custom_nginx=False,
    )
    create_site_users(site)

    Domain.objects.create(site=site, domain="{}.sites.tjhsst.edu".format(username))

    if not isinstance(user, str):
        site.group.users.add(user)

    make_site_dirs(site)
    create_config_files(site)
    if not batch:
        flush_permissions()
        reload_nginx_config()
    return site
