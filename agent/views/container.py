import os
import os.path
import subprocess
from random import choice
import lxc
from agent import rpc


def make_random_chars(l=32, allowed="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"):
    return "".join([choice(allowed) for i in range(l)])


def replace_in_file(fn, find, replace):
    # Am I the worst or what
    with open(fn) as f:
        x = f.read()
    x = x.replace(find, replace)
    with open(fn, "w") as f:
        f.write(x)


@rpc.method("container.create")
def create_container(name, template="debian"):
    script_path = "/var/conductor/{}/create".format(template)
    container = lxc.Container(name)
    if container.defined:
        return 2, ""

    proc = subprocess.Popen([script_path, name], stdout=subprocess.PIPE)
    exit_code = proc.wait()
    uuid = proc.stdout.read().strip().decode()
    if exit_code:
        return 1, ""

    return 0, uuid


@rpc.method("container.state")
def container_state(name):
    container = lxc.Container(name)
    if not container.defined:
        return 2  # Container does not exist
    if not container.running:
        return 1  # Container is not running
    return 0  # Container exists and is running


@rpc.method("container.power")
def container_power(name, state, timeout=15):
    container = lxc.Container(name)
    if not container.defined:
        return 2  # Container does not exist
    if state == 0:  # Power off the container
        if not container.running:
            return 1  # Request already satisfied
        result = container.attach_wait(lxc.attach_run_command, ["/conductor/power-off"])
        if not result:
            if not container.shutdown(timeout):
                container.stop()
        if result:
            container.stop()
        return 0  # The container was stopped, somehow
    if state == 1:  # Power on the container
        if container.running:
            return 1  # The container is already running
        if container.start():
            return 0  # The container has been started
        else:
            return -1  # There was a problem changing the container state


@rpc.method("container.destroy")
def container_destroy(name):
    error = container_power(name, 0)
    if error and error != 1:
        return error

    container = lxc.Container(name)
    if not container.destroy():
        return -1  # There was a problem changing the container state
    return 0  # Container was destroyed


@rpc.method("container.ips")
def container_ips(name):
    container = lxc.Container(name)
    if not container.defined:
        return 3, []
    if not container.running:
        return 2, []
    ips = container.get_ips(timeout=5)
    if not ips:
        return 1, []
    return 0, ips


@rpc.method("container.set_hostname")
def container_set_hostname(name, new_hostname):
    container = lxc.Container(name)
    if not container.defined:
        return 3
    if not container.set_config_item("lxc.utsname", new_hostname):
        return 1
    container.attach_wait(lxc.attach_run_command, ["/conductor/set-hostname", new_hostname])
    return 0


@rpc.method("container.reset_root_password")
def container_reset_root(name):
    container = lxc.Container(name)
    if not container.defined:
        return 3, ""
    if not container.running:
        return 2, ""
    newpasswd = make_random_chars()
    if container.attach_wait(lxc.attach_run_command, ["/bin/sh", "-c", "echo root:{} | chpasswd".format(newpasswd)]):
        return 1, ""
    return 0, newpasswd


@rpc.method("container.exec_shell")
def container_execute_shell_command(name, command):
    container = lxc.Container(name)
    if not container.defined:
        return 3, 255
    if not container.running:
        return 2, 255
    result = container.attach_wait(lxc.attach_run_command, ["/bin/sh", "-c", command])
    if result:
        return 1, result
    return 0, 0


@rpc.method("container.dump_config")
def container_dump_config(name):
    container = lxc.Container(name)
    if not container.defined:
        return 1, ""
    with open(container.config_file_name) as f:
        return 0, [[k.strip() for k in j.split("=")] for j in [i.strip() for i in f.readlines()] if not (j.startswith("#") or "=" not in j)]


@rpc.method("container.management_actions")
def management_actions(name):
    rootfs = dict(container_dump_config(name)[1])["lxc.rootfs"]
    p = os.path.join(rootfs, "conductor/actions")
    if not os.path.exists(p):
        return []
    with open(p) as f:
        return [i.strip() for i in f.readlines() if i.strip()]


@rpc.method("container.run_action")
def container_run_action(name, action):
    p = os.path.join("/conductor/action", action)
    container = lxc.Container(name)
    if container.attach_wait(lxc.attach_run_command, ["/bin/sh", "-c", p]):
        return False
    return True


@rpc.method("container.list")
def container_list():
    return lxc.list_containers()
