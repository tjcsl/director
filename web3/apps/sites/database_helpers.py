import psycopg2
import MySQLdb
from _mysql_exceptions import ProgrammingError as MySQLProgrammingError, OperationalError as MySQLOperationalError

from django.conf import settings
from django.core.cache import cache

from .helpers import run_as_site

from raven.contrib.django.raven_compat.models import client


def create_postgres_database(database):
    conn = psycopg2.connect("host = '{}' dbname='postgres' user='{}' password='{}'".format(
        settings.POSTGRES_DB_HOST, settings.POSTGRES_DB_USER, settings.POSTGRES_DB_PASS))
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM pg_catalog.pg_user WHERE usename = '{}'".format(database.username))
        if cursor.rowcount == 0:
            cursor.execute("CREATE USER \"{}\" WITH PASSWORD \'{}\'".format(database.username, database.password))
        else:
            cursor.execute("ALTER USER \"{}\" WITH PASSWORD '{}'".format(database.username, database.password))
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = '{}'".format(database.db_name))
        if cursor.rowcount == 0:
            cursor.execute("CREATE DATABASE \"{}\" WITH OWNER = \"{}\"".format(database.db_name, settings.POSTGRES_DB_USER))
        cursor.execute("GRANT ALL PRIVILEGES ON DATABASE \"{}\" TO \"{}\"".format(database.db_name, database.username))
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
        cursor.execute("GRANT ALL ON SCHEMA public TO \"{}\"".format(database.username))
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
        cursor.execute("ALTER USER \"{}\" WITH PASSWORD \'{}\'".format(database.username, database.password))
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
        cursor.execute("DROP DATABASE IF EXISTS \"{}\"".format(database.db_name))
        cursor.execute("DROP USER IF EXISTS \"{}\"".format(database.username))
        return True
    except psycopg2.OperationalError:
        client.captureException()
        return False
    finally:
        conn.close()


def list_tables(database):
    try:
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
    except:
        client.captureException()
    return None


def create_mysql_database(database):
    conn = MySQLdb.connect(host=settings.MYSQL_DB_HOST, user=settings.MYSQL_DB_USER, password=settings.MYSQL_DB_PASS)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM mysql.user WHERE user = '{}'".format(database.username))
        if cursor.rowcount == 0:
            cursor.execute("CREATE USER '{}'@'%' IDENTIFIED BY '{}';".format(database.username, database.password))
        cursor.execute("CREATE DATABASE IF NOT EXISTS {};".format(database.db_name))
        cursor.execute("GRANT ALL ON {} . * TO '{}';".format(database.db_name, database.username))
        cursor.execute("FLUSH PRIVILEGES;")
        return True
    except (MySQLProgrammingError, MySQLOperationalError):
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
        cursor.execute("DROP DATABASE IF EXISTS '{}';".format(database.db_name))
        cursor.execute("DROP USER '{}'@'%';".format(database.username))
        return True
    except MySQLProgrammingError:
        client.captureException()
        return False
    finally:
        conn.close()


def get_sql_version(site):
    key = "site:database:version:{}".format(site.database.category)
    obj = cache.get(key)
    if obj:
        return obj

    if site.database.category == "mysql":
        ret, out, err = run_as_site(site, ["mysql", "--version"])
        cache.set(key, out)
        return out
    else:
        ret, out, err = run_as_site(site, ["psql", "--version"])
        cache.set(key, out)
        return out
