from typing import Callable
from .interface import PushInterface
from .exceptions import PushServiceRequestException
import requests
import logging


class ServerChan(PushInterface):
    def __init__(self, **kwargs) -> None:
        self.key = kwargs.get("key")
        self.channel = kwargs.get("channel", None)
        self.session = requests.Session()
        super().__init__()

    def send(self, title, message) -> None:
        logging.debug(f"Pushing message title={title}, message={message}")
        payload = {
            "title": title,
            "desp": message,
        }
        if self.channel and self.channel != "":
            payload['channel'] = self.channel
        try:
            res = self.session.post(
                f"https://sctapi.ftqq.com/{self.key}.send", data=payload)
            response = res.json()
            if response['code'] != 0:
                raise PushServiceRequestException(response["message"])
        except PushServiceRequestException as e:
            raise e
        except Exception as e:
            raise PushServiceRequestException(e)

    def get_callback(self) -> Callable:
        def callback(title, message):
            return self.send(title, message)
        return callback
