from social.backends.oauth import BaseOAuth2
from social.pipeline.user import get_username as social_get_username

from ...utils.tjldap import get_uid
from ..users.models import Group


def get_username(strategy, details, user=None, *args, **kwargs):
    result = social_get_username(strategy, details, user=user, *args, **kwargs)
    return result


def create_user_group(strategy, details, user, *args, **kwargs):
    try:
        group = Group.objects.get(id=user.id)
    except Group.DoesNotExist:
        group = Group.objects.create(id=user.id, service=user.service, name=user.username)
        group.users.add(user.pk)
    group.save()
    return {"group": group}


class IonOauth2(BaseOAuth2):
    name = 'ion'
    AUTHORIZATION_URL = 'https://ion.tjhsst.edu/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://ion.tjhsst.edu/oauth/token'
    ACCESS_TOKEN_METHOD = 'POST'

    def get_user_details(self, response):
        profile = self.get_json('https://ion.tjhsst.edu/api/profile',
                                params={'access_token': response['access_token']})
        is_admin = profile['is_eighth_admin']
        # fields used to populate/update User model
        return {
            'username': profile['ion_username'],
            'id': get_uid(profile['ion_username']),
            'email': profile['tj_email'],
            'service': False,
            'is_admin': is_admin,
            'is_superuser': is_admin,
            'is_staff': is_admin
        }

    def get_user_id(self, details, response):
        return details['id']
