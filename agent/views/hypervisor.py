from agent import rpc

# parsing procfs is fun


@rpc.method("hypervisor.load_average")
def hypervisor_load_average():
    with open("/proc/loadavg") as f:
        return [float(i) for i in f.read().strip().split()[:3]]


@rpc.method("hypervisor.memory")
def hypervisor_memory():
    with open("/proc/meminfo") as f:
        data = dict([[j.strip().split()[0] for j in i.strip().split(":")] for i in f.readlines()])
        for i in data:
            # it could've been great
            data[i] = float(data[i])
    return [data["MemFree"], data["MemAvailable"]]
