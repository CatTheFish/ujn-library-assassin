import os
from PIL import ImageFont


def extract_value_with_specific_prefix(dic: dict, prefix: str, bool_val_list: list) -> dict:
    config = {}
    for key in dic.keys():
        if key.startswith(prefix):
            config[key.replace(prefix, "").lower()] = dic.get(key)
    for key in bool_val_list:
        if key in dic:
            dic[key] = dic[key].lower() == "true"
    return config


def extract_captcha_config():
    config = {}
    if os.environ.get("CAPTCHA_SERVICE") == "chaojiying":
        config = extract_value_with_specific_prefix(
            os.environ, "CHAOJIYING.", ["record_img"])
        # Check whether font is available
        ImageFont.truetype(config.get("font"))
    return config


def extract_push_config():
    config = {}
    if os.environ.get("PUSH_SERVICE") == "serverchan":
        config = extract_value_with_specific_prefix(
            os.environ, "SERVERCHAN.", [])
    return config
