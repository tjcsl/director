import os
import shutil
import stat
import time

import shlex
from subprocess import Popen, check_output, PIPE, CalledProcessError
from threading import Timer

from .models import Site
from ..users.models import User, Group

from django.template.loader import render_to_string

from raven.contrib.django.raven_compat.models import client


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
    site.user = user
    site.group = group
    site.save()
    return (user, group)


def get_next_id():
    if User.objects.filter(service=True).count() == 0:
        return 10000
    return list(User.objects.filter(service=True).order_by('id'))[-1].id + 1


def make_site_dirs(site):
    for i in ["", "public", "private"]:
        path = os.path.join(site.path, i)
        if not os.path.exists(path):
            os.makedirs(path)
        os.chown(path, site.user.id, site.group.id)
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP | stat.S_ISGID)
    Popen("/usr/bin/setfacl -m u:www-data:rx {}".format(site.path).split())
    Popen("/usr/bin/setfacl -m u:www-data:rx {}".format(os.path.join(site.path, "public")).split())


def create_config_files(site):
    if not site.custom_nginx:
        with open("/etc/nginx/director.d/{}.conf".format(site.name), "w+") as f:
            f.write(render_to_string("config/nginx.conf", {"site": site}))
    if site.category == "php":
        with open("/etc/php/7.0/fpm/pool.d/{}.conf".format(site.name), "w+") as f:
            f.write(render_to_string("config/phpfpm.conf", {"site": site}))
    elif site.category == "dynamic" and hasattr(site, "process"):
        create_process_config(site.process)


def write_new_index_file(site):
    with open(os.path.join(site.path, "public", "index.html"), "w+") as f:
        f.write(render_to_string("config/index.html", {"site": site}))


def delete_site_files(site):
    files = ["/etc/nginx/director.d/{}.conf", "/etc/php/7.0/fpm/pool.d/{}.conf", "/etc/supervisor/director.d/{}.conf"]
    files = [x.format(site.name) for x in files]
    for f in files:
        if os.path.isfile(f):
            try:
                os.remove(f)
            except OSError:
                client.captureException()
    try:
        shutil.rmtree(site.path)
    except FileNotFoundError:
        client.captureException()


def create_process_config(process):
    with open("/etc/supervisor/director.d/{}.conf".format(process.site.name), "w+") as f:
        f.write(render_to_string("config/supervisor.conf", {"process": process}))


def delete_process_config(process):
    filename = "/etc/supervisor/director.d/{}.conf".format(process.site.name)
    if os.path.isfile(filename):
        os.remove(filename)


def restart_supervisor(site):
    try:
        site.process
        Popen("supervisorctl restart {}".format(site.name).split())
    except Site.process.RelatedObjectDoesNotExist:
        pass


def get_supervisor_status(site):
    if not hasattr(site, "process"):
        return "No Process"

    try:
        return check_output("supervisorctl status {}".format(site.name).split()).decode()
    except CalledProcessError:
        client.captureException()
        return "Status Retrieval Failure"


def reload_services():
    Popen("systemctl reload nginx.service".split())
    Popen("systemctl restart php7.0-fpm.service".split())
    Popen("supervisorctl update".split())


def reload_nginx_config():
    Popen("/usr/sbin/nginx -s reload".split())


def check_nginx_config():
    return Popen(["/usr/sbin/nginx", "-t"]).wait() == 0


def flush_permissions():
    if os.path.isfile("/proc/net/rpc/auth.unix.gid/flush"):
        with open("/proc/net/rpc/auth.unix.gid/flush", "w") as f:
            f.write(str(int(time.time())))
    Popen("/usr/sbin/nscd -i group".split())
    Popen("/usr/sbin/nscd -i passwd".split())


def run_as_site(site, cmd, cwd=None, env=None, timeout=15):
    proc = Popen(shlex.split(cmd) if isinstance(cmd, str) else cmd, preexec_fn=demote(
        site.user.id, site.group.id), cwd=cwd or site.path, env=env, stdout=PIPE, stderr=PIPE)
    timer = Timer(timeout, lambda p: p.terminate(), [proc])
    try:
        timer.start()
        out, err = proc.communicate()
    finally:
        timer.cancel()
    return (proc.returncode, out.decode("utf-8", "replace"), err.decode("utf-8", "replace"))


def demote(uid, gid):
    def result():
        os.setgroups([gid])
        os.setgid(gid)
        os.setuid(uid)
    return result


def generate_ssh_key(site, overwrite=True):
    sshpath = os.path.join(site.private_path, ".ssh")
    keypath = os.path.join(sshpath, "id_rsa")
    if not os.path.exists(sshpath):
        os.makedirs(sshpath)
    os.chown(sshpath, site.user.id, site.group.id)
    os.chmod(sshpath, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    if os.path.isfile(keypath):
        if not overwrite:
            return False
        os.remove(keypath)
    if os.path.isfile(keypath + ".pub"):
        os.remove(keypath + ".pub")

    output = run_as_site(site, ["/usr/bin/ssh-keygen", "-t", "rsa", "-b", "4096", "-N", "", "-f", keypath])

    if not output[0] == 0:
        raise IOError("Could not generate RSA keys ({}) - {} - {}".format(output[0], output[1], output[2]))

    os.chown(keypath, site.user.id, site.group.id)
    os.chown(keypath + ".pub", site.user.id, site.group.id)
    os.chmod(keypath, stat.S_IRUSR | stat.S_IWUSR)
    os.chmod(keypath + ".pub", stat.S_IRUSR | stat.S_IWUSR)
    return True


def do_git_pull(site):
    fix_permissions(site)
    output = run_as_site(site, "git pull", cwd=site.public_path, env={
        "GIT_SSH_COMMAND": "ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i {}".format(os.path.join(site.private_path, ".ssh/id_rsa")),
        "HOME": site.private_path
    })
    if site.category == "dynamic":
        restart_supervisor(site)
    return output


def get_latest_commit(site):
    try:
        output = run_as_site(site, ["git", "log", "-n", "1"], cwd=site.public_path)
    except:
        client.captureException()
        return "Error"
    if not output[0] == 0:
        return "Error - {}".format(output[2].replace("\n", " ").replace("\r", ""))
    return output[1]


def fix_permissions(site):
    for root, dirs, files in os.walk(site.path):
        dirs[:] = [d for d in dirs if not d == ".ssh"]
        for f in files + dirs:
            path = os.path.join(root, f)
            try:
                st = os.lstat(path)
            except FileNotFoundError:
                client.captureException()
                continue
            os.lchown(path, site.user.id, site.group.id)
            if stat.S_ISLNK(st.st_mode):
                pass
            elif stat.S_ISDIR(st.st_mode):
                os.chmod(path, st.st_mode | stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP)
            else:
                os.chmod(path, st.st_mode | stat.S_IRGRP | stat.S_IWGRP)


def list_executable_files(path, level):
    path = path.rstrip(os.path.sep)
    num_sep = path.count(os.path.sep)
    out = []

    for root, dirs, files in os.walk(path):
        # ignore hidden files and folders, ignore common npm install path
        files = [f for f in files if not f[0] == "."]
        dirs[:] = [d for d in dirs if not d[0] == "." and not d == "node_modules"]

        # ignore files in virtual environments
        if "pip-selfcheck.json" in files:
            del dirs[:]
            continue

        for f in files:
            p = os.path.abspath(os.path.join(root, f))
            if os.access(p, os.X_OK):
                out.append(p)

        # limit folder recursion
        cur_num_sep = root.count(os.path.sep)
        if num_sep + level <= cur_num_sep:
            del dirs[:]

    return out
