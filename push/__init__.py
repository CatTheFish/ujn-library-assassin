from .server_chan import ServerChan
from .dummy import Dummy
from .interface import PushInterface
from .exceptions import *


def get_push_service(service, config) -> PushInterface:
    if service == "serverchan":
        return ServerChan(**config)
    return Dummy()
