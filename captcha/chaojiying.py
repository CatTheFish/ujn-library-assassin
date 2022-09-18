import logging
from .interface import CaptchaInterface
from .exceptions import *
from Crypto.Hash.MD5 import MD5Hash
import requests
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO


class Chaojiying(CaptchaInterface):
    def __init__(self, **kwargs) -> None:
        md5 = MD5Hash()
        md5.update(kwargs.get("password").encode("utf-8"))
        self.username = kwargs.get("username")
        self.password = md5.digest().hex()
        self.app_id = kwargs.get("softid")
        self.font = kwargs.get("font")
        self.record_img = kwargs.get("record_img", False)
        self.session = requests.Session()
        super().__init__()

    def get_captcha_result(self, img, target, points_expected=None) -> tuple:
        img = Image.open(BytesIO(img))
        target = Image.open(BytesIO(target))
        width, height = img.size
        font_size = 20
        font_margin = 5
        new_img = Image.new(
            'RGB', (width, height + target.size[1] + font_size + font_margin * 2), (255, 255, 255))
        new_img.paste(img)
        # Append hint text to new image
        draw = ImageDraw.Draw(new_img)
        font = ImageFont.truetype(self.font, font_size)
        draw.text((font_margin, height + font_margin),
                  "请依次点击下列字符", (0, 0, 0), font=font)
        new_img.paste(target, (0, height + font_size + font_margin * 2))
        new_img_bytes = BytesIO()
        new_img.save(new_img_bytes, format="JPEG")
        new_img_bytes.seek(0)
        # Post image for cloud recognation
        payload = {
            "user": (None, self.username),
            "pass2": (None, self.password),
            "softid": (None, self.app_id),
            "codetype": (None, 9004),
            "userfile": ("1.jpg", new_img_bytes)
        }
        res = self.session.post(
            "http://upload.chaojiying.net/Upload/Processing.php", files=payload)
        try:
            response = res.json()
            if response['err_no'] != 0:
                raise CaptchaBusinessError(response['err_str'])
            points = []
            for point in response['pic_str'].split("|"):
                coordinate = point.split(",")
                points.append({
                    "x": int(coordinate[0]),
                    "y": int(coordinate[1])
                })
            if self.record_img:
                for i in range(len(points)):
                    draw.text((points[i]["x"] - font_size / 2, points[i]["y"] - font_size / 2),
                              str(i+1), (255, 0, 0), font=font)
                new_img.save(f"logs/{response['pic_id']}.jpg")
            # If number of points presents, check whether the number is match
            if points_expected and points_expected != len(points):
                raise CaptchaResultError(
                    "Points mismatch", id=response['pic_id'])
            return response['pic_id'], points
        except CaptchaResultError as e:
            raise e
        except CaptchaBusinessError as e:
            raise e
        except Exception as e:
            raise CaptchaRequestError(e)

    def report_error(self, id, error) -> list:
        payload = {
            "user": self.username,
            "pass2": self.password,
            "id": id,
            "softid": self.app_id
        }
        res = self.session.post(
            "http://upload.chaojiying.net/Upload/ReportError.php", data=payload)
        try:
            response = res.json()
            if response['err_no'] != 0:
                logging.warning(
                    f"Unable to report bad captcha {response['err_str']}")
                raise CaptchaRequestError(response['err_str'])
            logging.warning(f"Reported bad captcha: {id}")
        except Exception as e:
            raise CaptchaRequestError(e)
