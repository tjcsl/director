import contextlib
import os


@contextlib.contextmanager
def switch_user_group(uid: int, gid: int):
    groups = list(os.getgroups())

    os.setresgid(0, gid, 0)
    os.setgroups([gid])
    os.setresuid(0, uid, 0)

    try:
        yield
    finally:
        os.setresuid(0, 0, 0)
        os.setresgid(0, 0, 0)
        os.setgroups([0] + groups)


def switch_to_site_user(site):
    return switch_user_group(site.user.id, site.group.id)
