from agent import rpc
import platform

@rpc.method("ping.ping")
def ping():
    """
    RPC: ping.ping
    Always responds with {"ok": True}, for testing purposes.
    """
    return dict(ok=True)

@rpc.method("ping.os")
def os():
    """
    RPC: ping.os
    """
    return "{} {}".format(platform.system(), platform.release())
