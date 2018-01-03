import os
import shutil
import stat
import time

import shlex
from subprocess import Popen, check_output, PIPE, CalledProcessError
from threading import Timer

from .models import Site
from ..users.models import User, Group

from django.conf import settings
from django.utils.crypto import get_random_string
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


def add_access_token(func):
    """Decorator to add an access token if it is not set.

    Used to ensure that the user can authenticate with the Node.js server for cases like the web terminal.
    """
    def func_wrapper(request, **kwargs):
        if not request.user.access_token:
            request.user.access_token = get_random_string(24)
            request.user.save()
        return func(request, **kwargs)
    return func_wrapper


def get_next_id():
    if User.objects.filter(service=True).count() == 0:
        return 10000
    return User.objects.filter(service=True).order_by('-id')[0].id + 1


def make_site_dirs(site):
    for i in ["", "public", "private"]:
        path = os.path.join(site.path, i)
        if not os.path.exists(path):
            os.makedirs(path)
        os.chown(path, site.user.id, site.group.id)
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP | stat.S_ISGID)
    Popen(["/usr/bin/setfacl", "-m", "u:www-data:rx", site.path])
    Popen(["/usr/bin/setfacl", "-m", "u:www-data:rx", os.path.join(site.path, "public")])


def create_config_files(site):
    if not site.custom_nginx:
        with open("/etc/nginx/director.d/{}.conf".format(site.name), "w+") as f:
            f.write(render_to_string("config/nginx.conf", {"site": site}))
    if site.category == "php":
        with open("/etc/php/7.0/fpm/pool.d/{}.conf".format(site.name), "w+") as f:
            f.write(render_to_string("config/phpfpm.conf", {"site": site}))
    elif site.category == "dynamic" and hasattr(site, "process"):
        create_process_config(site.process)


def delete_php_config(site):
    filename = "/etc/php/7.0/fpm/pool.d/{}.conf".format(site.name)
    if os.path.exists(filename):
        os.remove(filename)


def write_new_index_file(site):
    """Creates a default index file for new sites."""
    with open(os.path.join(site.path, "public", "index.html"), "w+") as f:
        f.write(render_to_string("config/index.html", {"site": site}))


def delete_site_files(site):
    """Deletes all site content and configuration files."""
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
    except Exception:
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
        Popen(["supervisorctl", "restart", site.name])
    except Site.process.RelatedObjectDoesNotExist:
        pass


def get_supervisor_status(site):
    if not hasattr(site, "process"):
        return "No Process"

    try:
        return check_output(["supervisorctl", "status", site.name]).decode()
    except CalledProcessError:
        client.captureException()
        return "Status Retrieval Failure"


def get_supervisor_statuses(sites):
    try:
        out = check_output(["supervisorctl", "status"] + sites).decode()
    except CalledProcessError:
        client.captureException()
        return {}
    statuses = {}
    for line in out.split("\n"):
        line = line.strip()
        if not line:
            continue
        key, value = line.split(" ", 1)
        statuses[key] = True if "RUNNING" in value else False
    return statuses


def reload_services():
    a = reload_nginx_config()
    b = reload_php_fpm()
    c = update_supervisor()
    return a and b and c


def root_exec(cmd):
    p = Popen(shlex.split(cmd) if isinstance(cmd, str) else cmd, stdout=PIPE, stderr=PIPE)
    output = p.stdout.read()
    error = p.stderr.read()
    if p.wait() == 0:
        return True
    else:
        client.captureMessage("Failed to execute command: {}".format(cmd), extra={
            "stdout": output,
            "stderr": error
        })
        return False


def update_supervisor():
    a = root_exec(["supervisorctl", "reread"])
    b = root_exec(["supervisorctl", "update"])
    return a and b


def reload_php_fpm():
    if root_exec(["systemctl", "reload", "php7.0-fpm"]):
        return root_exec(["systemctl", "restart", "php7.0-fpm"])
    return False


def reload_nginx_config():
    if root_exec(["/usr/sbin/nginx", "-t"]):
        return root_exec(["/usr/sbin/nginx", "-s", "reload"])
    return False


def check_nginx_config():
    return Popen(["/usr/sbin/nginx", "-t"]).wait() == 0


def flush_permissions():
    """Resets any cached users or groups."""
    if os.path.isfile("/proc/net/rpc/auth.unix.gid/flush"):
        with open("/proc/net/rpc/auth.unix.gid/flush", "w") as f:
            f.write(str(int(time.time())))
    Popen(["/usr/sbin/nscd", "-i", "group"])
    Popen(["/usr/sbin/nscd", "-i", "passwd"])


def run_as_site(site, cmd, cwd=None, env=None, timeout=15):
    """Runs a command as a specific user."""
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
    """Generate an ssh key for a site user."""
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
    """Perform a git pull on a certain site."""
    fix_permissions(site)
    output = run_as_site(site, "git pull", cwd=site.git_path, env={
        "GIT_SSH_COMMAND": "ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i {}".format(os.path.join(site.private_path, ".ssh/id_rsa")),
        "HOME": site.private_path
    })
    if site.category == "dynamic":
        restart_supervisor(site)
    return output


def get_latest_commit(site):
    """Get the latest commit in the git repository inside the site."""
    try:
        output = run_as_site(site, ["git", "log", "-n", "1"], cwd=site.git_path)
    except Exception:
        client.captureException()
        return "Error"
    if not output[0] == 0:
        return "Error - {}".format(output[2].replace("\n", " ").replace("\r", ""))
    return output[1]


def fix_permissions(site):
    """Makes sure that all files are owned by the site user and the site group has access."""
    for root, dirs, files in os.walk(site.path):
        dirs[:] = [d for d in dirs if not d == ".ssh"]
        for f in files + dirs:
            path = os.path.join(root, f)
            try:
                st = os.lstat(path)
            except Exception:
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


def clean_site_type(instance):
    """Destroy any old site configuration caused by changing site types."""
    if instance.category != "php":
        delete_php_config(instance)

    if instance.category != "dynamic" and hasattr(instance, "process"):
        instance.process.delete()

    if instance.category != "vm" and hasattr(instance, "virtual_machine"):
        vm = instance.virtual_machine
        vm.site = None
        vm.save()


def generate_ssl_certificate(domain, renew=False):
    """Generate SSL certs for a domain and update the nginx config."""
    process = Popen([
        "/usr/bin/certbot",
        "certonly",
        "--webroot",
        "-w",
        settings.LE_WEBROOT,
        "-d",
        domain.domain,
        "-n"
    ], stdout=PIPE, stderr=PIPE)

    success = process.wait() == 0

    if success:
        if not renew:
            create_config_files(domain.site)
            reload_services()
    else:
        client.captureMessage("Failed to generate SSL certificate for domain {} on site {}".format(domain.domain, domain.site.name), extra={
            "stdout": process.stdout.read(),
            "stderr": process.stderr.read()
        })
