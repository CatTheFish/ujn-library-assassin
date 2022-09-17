from typing import Callable


class PushInterface:
    def send(self, title, message) -> None:
        pass

    def get_callback(self) -> Callable:
        pass
