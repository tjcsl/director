from .models import User, Group
from ..sites.models import Site
from ..sites.helpers import create_site_users, make_site_dirs, create_config_files, flush_permissions
from ...utils.tjldap import get_uid


def create_user(request, username):
    if User.objects.filter(username=username).exists():
        return User.objects.get(username=username)

    try:
        uid = get_uid(username)
    except IndexError:
        return None

    profile = request.user.api_request("profile/{}".format(user.username))

    user = User.objects.create(
        id=uid,
        username=username,
        full_name=profile.get("common_name", ""),
        email=profile.get("tj_email", "{}@tjhsst.edu".format(username)),
        is_staff=profile.get("is_teacher", False),
        is_superuser=profile.get("is_eighth_admin", False)
    )

    if not Group.objects.filter(id=user.id).exists():
        group = Group.objects.create(id=user.id, service=False, name=user.username)
        group.users.add(user.pk)
        group.save()

    return user


def create_webdocs(user):
    if Site.objects.filter(name=user.username).exists():
        return Site.objects.get(name=user.username)

    site = Site.objects.create(
        name=user.username,
        description=user.full_name,
        domain="{}.sites.tjhsst.edu".format(user.username),
        category="php",
        purpose="user",
        custom_nginx=False
    )
    create_site_users(site)
    site.group.users.add(user)

    make_site_dirs(site)
    crate_config_files(site)
    flush_permissions()
    return site
