from urllib import request
from urllib.parse import urljoin
from requests import Session
from bs4 import BeautifulSoup
import random
from .exceptions import *
import logging
import json
from base64 import b64encode

headers_common = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36"
}


class LeoLibWeb:
    def __init__(self, baseurl, username, password) -> None:
        self.baseurl = baseurl
        self.username = username
        self.password = password
        self.session = Session()
        self.session.get(baseurl)
        self.csrfToken = ""
        self.csrfUri = ""

    def init_login_synchorizer(self) -> None:
        self.csrfToken, self.csrfUri = self.__extract_synchorizer_info(
            "/login")

    def init_booking_synchorizer(self) -> None:
        self.csrfToken, self.csrfUri = self.__extract_synchorizer_info("/self")

    def __extract_synchorizer_info(self, uri) -> tuple:
        res = self.session.get(
            urljoin(self.baseurl, uri), headers=headers_common)
        if res.status_code != 200:
            raise LeoLibWebRequestError(res.text)
        html = res.text
        soup = BeautifulSoup(html, "html.parser")
        token = soup.find('input', {'name': 'SYNCHRONIZER_TOKEN'}).get('value')
        uri = soup.find('input', {'name': 'SYNCHRONIZER_URI'}).get('value')
        logging.debug(
            f"[{self.username}][login] synchorizer token={token}, uri={uri}")
        return token, uri

    def get_captcha_token(self, user_id=None, username=None, with_username=False) -> tuple:
        payload = {
            "userId": user_id or "",
            "username": username or ""
        }
        if with_username:
            payload['username'] = self.username
        # Request a captcha token
        res = self.session.post(
            urljoin(self.baseurl, "cap/captcha"), headers=headers_common, data=payload)
        if res.status_code != 200:
            raise LeoLibWebRequestError(res.text)
        response = res.json()
        if response['status'] != "OK":
            raise LeoLibWebCaptchaError(
                f"Unable to get captcha: {response.status}")
        token = response['token']
        checkCount = response['wordCheckCount']
        logging.debug(
            f"[{self.username}][captcha] token={token}, workCheckCount={checkCount}")
        return token, checkCount

    def get_captcha_img(self, token) -> tuple:
        # Download pictures as buffer
        res = self.session.get(urljoin(self.baseurl, "cap/captchaImg/1"), params={
            "token": token,
            "r": random.random()
        }, headers=headers_common)
        if res.status_code != 200:
            raise LeoLibWebRequestError(res.text)
        captcha_img = res.content
        res = self.session.get(urljoin(self.baseurl, "cap/captchaImg/2"), params={
            "token": token,
            "r": random.random()
        }, headers=headers_common)
        if res.status_code != 200:
            raise LeoLibWebRequestError(res.text)
        captcha_target = res.content
        return captcha_img, captcha_target

    def submit_captcha_result(self, token, result, user_id=None) -> None:
        result_str = json.dumps(result)
        payload = {
            "a": b64encode(result_str.encode()),
            "token": token,
            "userId": user_id or ""
        }
        res = self.session.get(urljoin(
            self.baseurl, "cap/checkCaptcha"), params=payload, headers=headers_common)
        if res.status_code != 200:
            raise LeoLibWebRequestError(res.text)
        try:
            response = res.json()
            if "status" not in response or response['status'] != 'OK':
                if "message" in response:
                    raise LeoLibWebCaptchaError(response['message'])
                else:
                    raise LeoLibWebCaptchaError("Captcha error")
        except Exception as e:
            raise LeoLibWebCaptchaError(e)

    def login(self, captcha_token) -> None:
        payload = {
            "SYNCHRONIZER_TOKEN": self.csrfToken,
            "SYNCHRONIZER_URI": self.csrfUri,
            "username": self.username,
            "password": self.password,
            "authid": captcha_token
        }
        headers = {
            **{"Referer": urljoin(self.baseurl, "/login")}, **headers_common}
        res = self.session.post(urljoin(
            self.baseurl, "auth/signIn"), data=payload, headers=headers, allow_redirects=False)
        if res.status_code != 302:
            raise LeoLibWebRequestError(res.text)
        if "/login" in res.headers.get("Location") or "/auth/index" in res.headers.get("Location"):
            raise LeoLibWebAuthenticationError("Failed to authenticate")

    def book(self, captcha_token, date, seat, start, end) -> None:
        payload = {
            "SYNCHRONIZER_TOKEN": self.csrfToken,
            "SYNCHRONIZER_URI": self.csrfUri,
            "date": date,
            "seat": seat,
            "start": start,
            "end": end,
            "authid": captcha_token
        }
        res = self.session.post(urljoin(self.baseurl, "selfRes"), headers={
                                **headers_common, **{"Referer": urljoin(self.baseurl, "self")}}, data=payload, allow_redirects=False)
        # Session dies or captcha expires
        if res.status_code != 200:
            raise LeoLibWebRequestError("Failed to book, redirected")
        if "预约失败" in res.text:
            if "请尽快选择其他时段或座位" in res.text:
                raise LeoLibWebSeatUnavailableError("Seat unavailable")
            else:
                raise LeoLibWebBookingUnavailableError(
                    "Booking seems unavailable")
        if "凭证号" not in res.text:
            raise LeoLibWebRequestError(f"Unknown error, {res.text}")
