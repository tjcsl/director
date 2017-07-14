import re
import pam

from django.conf import settings

from ..users.models import User


class PAMAuthenticationBackend(object):
    """Authenticate using PAM.

    This should only be used if Ion OAuth is unavailable.

    """

    def authenticate(self, username=None, password=None):
        if not isinstance(username, str) or password is None:
            return None

        if not settings.PASSWORD_AUTH:
            return None

        # remove all non-alphanumeric characters
        username = re.sub("\W", "", username)

        p = pam.pam()
        if p.authenticate(username, password, service="sshd"):
            try:
                return User.objects.get(username=username)
            except User.DoesNotExist:
                return None
        else:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
