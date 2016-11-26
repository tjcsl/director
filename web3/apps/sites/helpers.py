import os
import shutil
import stat
import time
import psycopg2
import MySQLdb
from _mysql_exceptions import ProgrammingError as MySQLProgrammingError, OperationalError as MySQLOperationalError

import shlex
from subprocess import Popen, check_output, PIPE, CalledProcessError
from threading import Timer

from django.conf import settings
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
    for i in ["{}", "{}public", "{}private"]:
        path = i.format(site.path)
        if not os.path.exists(path):
            os.makedirs(path)
        os.chown(path, site.user.id, site.group.id)
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
                 | stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP
                 | stat.S_ISGID)
    Popen("/usr/bin/setfacl -m u:www-data:rx {}".format(site.path).split())
    Popen("/usr/bin/setfacl -m u:www-data:rx {}public".format(site.path).split())


def create_config_files(site):
    if not site.custom_nginx:
        with open("/etc/nginx/director.d/{}.conf".format(site.name), "w+") as f:
            f.write(render_to_string("config/nginx.conf", {"site": site}))
    if site.category == "php":
        with open("/etc/php5/fpm/pool.d/{}.conf".format(site.name), "w+") as f:
            f.write(render_to_string("config/phpfpm.conf", {"site": site}))


def write_new_index_file(site):
    with open("{}public/index.html".format(site.path), "w+") as f:
        f.write(render_to_string("config/index.html", {"site": site}))


def delete_site_files(site):
    files = ["/etc/nginx/director.d/{}.conf", "/etc/php5/fpm/pool.d/{}.conf", "/etc/supervisor/director.d/{}.conf"]
    files = [x.format(site.name) for x in files]
    for f in files:
        if os.path.isfile(f):
            os.remove(f)
    shutil.rmtree(site.path)


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
    try:
        site.process
        return check_output("supervisorctl status {}".format(site.name).split()).decode()
    except CalledProcessError:
        client.captureException()
        return "Status Retrieval Failure"
    except Site.process.RelatedObjectDoesNotExist:
        return "No Process"


def reload_services():
    Popen("systemctl reload nginx.service".split())
    Popen("systemctl restart php5-fpm.service".split())
    Popen("supervisorctl update".split())


def reload_nginx_config():
    Popen("/usr/sbin/nginx -s reload".split())


def check_nginx_config():
    return Popen(["/usr/sbin/nginx", "-t"]).wait() == 0


def flush_permissions():
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
    return (proc.returncode, out.decode("utf-8"), err.decode("utf-8"))


def demote(uid, gid):
    def result():
        os.setgid(gid)
        os.setuid(uid)
    return result


def generate_ssh_key(site):
    sshpath = os.path.join(site.private_path, ".ssh")
    keypath = os.path.join(sshpath, "id_rsa")
    if not os.path.exists(sshpath):
        os.makedirs(sshpath)
    os.chown(sshpath, site.user.id, site.group.id)
    os.chmod(sshpath, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    if os.path.isfile(keypath):
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


def create_postgres_database(database):
    conn = psycopg2.connect("host = '{}' dbname='postgres' user='{}' password='{}'".format(
        settings.POSTGRES_DB_HOST, settings.POSTGRES_DB_USER, settings.POSTGRES_DB_PASS))
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM pg_catalog.pg_user WHERE usename = '{}'".format(database.username))
        if cursor.rowcount == 0:
            cursor.execute("CREATE USER {} WITH PASSWORD \'{}\'".format(database.username, database.password))
        else:
            cursor.execute("ALTER USER {} WITH PASSWORD '{}'".format(database.username, database.password))
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = '{}'".format(database.db_name))
        if cursor.rowcount == 0:
            cursor.execute("CREATE DATABASE {} WITH OWNER = {}".format(database.db_name, settings.POSTGRES_DB_USER))
        cursor.execute("GRANT ALL PRIVILEGES ON DATABASE {} TO {}".format(database.db_name, database.username))
    except psycopg2.DatabaseError:
        client.captureException()
        return False
    finally:
        conn.close()

    conn = psycopg2.connect("host = '{}' dbname='{}' user='{}' password='{}'".format(
        settings.POSTGRES_DB_HOST, database.db_name, settings.POSTGRES_DB_USER, settings.POSTGRES_DB_PASS))
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    try:
        cursor.execute("GRANT ALL ON SCHEMA public TO {}".format(database.username))
        return True
    except psycopg2.DatabaseError:
        client.captureException()
        return False
    finally:
        conn.close()


def change_postgres_password(database):
    conn = psycopg2.connect("host = '{}' dbname='postgres' user='{}' password='{}'".format(settings.POSTGRES_DB_HOST, settings.POSTGRES_DB_USER, settings.POSTGRES_DB_PASS))
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER USER {} WITH PASSWORD \'{}\'".format(database.username, database.password))
        return True
    except psycopg2.DatabaseError:
        client.captureException()
        return False
    finally:
        conn.close()


def delete_postgres_database(database):
    conn = psycopg2.connect("host = '{}' dbname='postgres' user='{}' password='{}'".format(
        settings.POSTGRES_DB_HOST, settings.POSTGRES_DB_USER, settings.POSTGRES_DB_PASS))
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    try:
        cursor.execute("DROP DATABASE IF EXISTS {}".format(database.db_name))
        cursor.execute("DROP USER IF EXISTS {}".format(database.username))
        return True
    except psycopg2.OperationalError:
        client.captureException()
        return False
    finally:
        conn.close()


def list_tables(database):
    if database.category == "postgresql":
        conn = psycopg2.connect("host = '{}' dbname='{}' user='{}' password='{}'".format(
            settings.POSTGRES_DB_HOST, database.db_name, settings.POSTGRES_DB_USER, settings.POSTGRES_DB_PASS))
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            return [table[0] for table in cursor.fetchall()]
        finally:
            conn.close()
    elif database.category == "mysql":
        conn = MySQLdb.connect(host=settings.MYSQL_DB_HOST, user=settings.MYSQL_DB_USER, password=settings.MYSQL_DB_PASS)
        cursor = conn.cursor()
        try:
            cursor.execute("SHOW TABLES IN {}".format(database.db_name))
            return [table[0] for table in cursor.fetchall()]
        finally:
            conn.close()
    return None


def create_mysql_database(database):
    conn = MySQLdb.connect(host=settings.MYSQL_DB_HOST, user=settings.MYSQL_DB_USER, password=settings.MYSQL_DB_PASS)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM mysql.user WHERE user = ''".format(database.username))
        if cursor.rowcount == 0:
            cursor.execute("CREATE USER '{}'@'%' IDENTIFIED BY '{}';".format(database.username, database.password))
        cursor.execute("CREATE DATABASE IF NOT EXISTS {};".format(database.db_name))
        cursor.execute("GRANT ALL ON {} . * TO {};".format(database.db_name, database.username))
        cursor.execute("FLUSH PRIVILEGES;")
        return True
    except MySQLProgrammingError:
        client.captureException()
        return False
    finally:
        conn.close()


def change_mysql_password(database):
    conn = MySQLdb.connect(host=settings.MYSQL_DB_HOST, user=settings.MYSQL_DB_USER, password=settings.MYSQL_DB_PASS)
    cursor = conn.cursor()
    try:
        cursor.execute("SET PASSWORD FOR '{}'@'%' = PASSWORD('{}');".format(database.username, database.password))
        cursor.execute("FLUSH PRIVILEGES;")
        return True
    except (MySQLProgrammingError, MySQLOperationalError):
        client.captureException()
        return False
    finally:
        conn.close()


def delete_mysql_database(database):
    conn = MySQLdb.connect(host=settings.MYSQL_DB_HOST, user=settings.MYSQL_DB_USER, password=settings.MYSQL_DB_PASS)
    cursor = conn.cursor()
    try:
        cursor.execute("DROP DATABASE IF EXISTS {};".format(database.db_name))
        cursor.execute("DROP USER '{}'@'%';".format(database.username))
        return True
    except MySQLProgrammingError:
        client.captureException()
        return False
    finally:
        conn.close()


def do_git_pull(site):
    if not settings.DEBUG:
        fix_permissions(site)
        output = run_as_site(site, "git pull", cwd=site.public_path, env={
            "GIT_SSH_COMMAND": "ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i {}".format(os.path.join(site.private_path, ".ssh/id_rsa")),
            "HOME": site.private_path
        })
        if site.category == "dynamic":
            restart_supervisor(site)
    else:
        output = (0, None, None)
    return output


def get_latest_commit(site):
    if not settings.DEBUG:
        output = run_as_site(site, ["git", "log", "-n", "1"], cwd=site.public_path)
        if not output[0] == 0:
            return "Error - {}".format(output[2].replace("\n", " ").replace("\r", ""))
        return output[1]
    else:
        return "commit 77f43ce5c319564fd781ac25dc24da022c3ce15b\nAuthor: Example User <none@none.com>\nDate:   Mon Jan 1 00:00:00 2016 -0000\nexample commit"


def fix_permissions(site):
    for root, dirs, files in os.walk(site.path):
        dirs[:] = [d for d in dirs if not d == ".ssh"]
        for f in files + dirs:
            path = os.path.join(root, f)
            st = os.stat(path)
            os.chown(path, site.user.id, site.group.id)
            if stat.S_ISDIR(st.st_mode):
                os.chmod(path, st.st_mode | stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP)
            else:
                os.chmod(path, st.st_mode | stat.S_IRGRP | stat.S_IWGRP)
