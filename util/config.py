import os
from PIL import ImageFont


def extract_captcha_config():
    config = {}
    if os.environ.get("CAPTCHA_SERVICE") == "chaojiying":
        for key in os.environ.keys():
            if "CHAOJIYING." in key:
                config[key.replace("CHAOJIYING.", "").lower()
                       ] = os.environ.get(key)
        config["record_img"] = config['record_img'].lower() == "true"
        # Check whether font is available
        ImageFont.truetype(config.get("font"))
    return config
