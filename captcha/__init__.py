from .chaojiying import Chaojiying
from .interface import CaptchaInterface
from .exceptions import *


def get_captcha_service(service, config) -> CaptchaInterface:
    if service == "chaojiying":
        return Chaojiying(**config)
    raise Exception(f"Unable to find captcha service named {service}")
