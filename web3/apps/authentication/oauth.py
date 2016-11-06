from social.backends.oauth import BaseOAuth2
from social.pipeline.user import get_username as social_get_username


def get_username(strategy, details, user=None, *args, **kwargs):
    result = social_get_username(strategy, details, user=user, *args, **kwargs)
    return result


class IonOauth2(BaseOAuth2):
    name = 'ion'
    AUTHORIZATION_URL = 'https://ion.tjhsst.edu/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://ion.tjhsst.edu/oauth/token'
    ACCESS_TOKEN_METHOD = 'POST'

    def get_user_details(self, response):
        profile = self.get_json('https://ion.tjhsst.edu/api/profile',
                                params={'access_token': response['access_token']})

        is_admin = profile['is_eighth_admin'] == "true"

        # fields used to populate/update User model
        return {'username': profile['ion_username'],
                'id': profile['id'],
                'email': profile['tj_email'],
                'service': False,
                'superuser': is_admin,
                'is_admin': is_admin,
                'is_superuser': is_admin,
                'is_staff': is_admin
                }

    def get_user_id(self, details, response):
        return details['id']
