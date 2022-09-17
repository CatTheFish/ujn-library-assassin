from typing import Callable
from .interface import PushInterface


class Dummy(PushInterface):
    def send(self, title, message) -> None:
        return

    def get_callback(self) -> Callable:
        def callback(title, message):
            return self.send(title, message)
        return callback
