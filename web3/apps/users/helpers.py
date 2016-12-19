from .models import User, Group
from ...utils.tjldap import get_uid


def create_user(request, username):
    user = User.objects.filter(username=username)
    if user.exists():
        return user

    try:
        uid = get_uid(username)
    except IndexError:
        return None

    profile = request.user.api_request("profile/{}".format(user.username), request=request)

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
