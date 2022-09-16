import logging
from threading import Thread
from captcha import *
from leo import *
from time import sleep, time
from datetime import datetime


def auto_retry(func):
    def wrapper(*args, **kwargs):
        while args[0].retry_remaining > 0:
            logging.debug(
                f"Auto retry: func={func.__name__}, remaining={args[0].retry_remaining}")
            try:
                return func(*args, **kwargs)
            except LeoLibWebAuthenticationError as e:
                raise e
            except LeoLibWebSeatUnavailableError as e:
                args[0].captcha_helper.stop()
                raise e
            except LeoLibWebBookingUnavailableError:
                # Sleep for 1 second
                sleep(1)
            except Exception as e:
                logging.error(e)
                args[0].retry_remaining = args[0].retry_remaining - 1
        if args[0].captcha_helper:
            args[0].captcha_helper.stop()
        raise Exception("Ran out of retries")
    return wrapper


class CaptchaHelper(Thread):
    def __init__(self, leo_api: LeoLibWeb, captcha: CaptchaInterface, token_expiration: int, retry_count: int) -> None:
        self.leo_api = leo_api
        self.captcha = captcha
        self.token_expiration = token_expiration
        self.token_store = []
        self.running = True
        self.retry_remaining = retry_count
        super().__init__(daemon=True)

    def run(self) -> None:
        while self.running:
            token_issue_time, token = self.issue_new_token()
            self.token_store.append((token_issue_time, token))
            sleep(self.token_expiration - 5)

    def get_token(self) -> str:
        while len(self.token_store) > 0:
            token_issue_time, token = self.token_store.pop()
            if token_issue_time + self.token_expiration < int(time()):
                return token
        token_issue_time, token = self.issue_new_token()
        return token

    def stop(self) -> None:
        logging.debug("Stopping captcha helper thread...")
        self.running = False

    @auto_retry
    def issue_new_token(self, with_username=True) -> tuple:
        token_issue_time = int(time())
        try:
            # Refresh captcha token
            token, check_count = self.leo_api.get_captcha_token(
                with_username=with_username)
            img, target = self.leo_api.get_captcha_img(token)
            captcha_recognition_id, points = self.captcha.get_captcha_result(
                img, target, check_count)
            self.leo_api.submit_captcha_result(token, points)
            # Store token along with issue time
            logging.debug(
                f"Got captcha token={token}, with_username={with_username}")
            return token_issue_time, token
        except CaptchaResultError as e:
            captcha_recognition_id = e.id
            logging.warning(
                f"Captcha code {captcha_recognition_id} mismatch, reporting...")
            if captcha_recognition_id:
                try:
                    self.captcha.report_error(captcha_recognition_id, e)
                except Exception as err:
                    logging.error(
                        f"Failed to report captcha code {captcha_recognition_id}, {err}")
            raise e
        except LeoLibWebCaptchaError as e:
            logging.warning(
                f"Captcha code {captcha_recognition_id} mismatch, not reporting...")
            raise e


class Booking(Thread):
    def __init__(self, leo_api: LeoLibWeb, captcha: CaptchaInterface, token_expiration: int, retry_count: int, seat: str, date: str, start: int, end: int) -> None:
        self.leo_api = leo_api
        self.captcha = captcha
        self.token_expiration = token_expiration
        self.captcha_helper = CaptchaHelper(
            leo_api, captcha, token_expiration, retry_count)
        self.retry_remaining = retry_count
        self.seat = seat
        self.date = date
        self.start_time = start
        self.end_time = end
        self.callback = lambda x: None
        super().__init__(daemon=True)

    @auto_retry
    def login(self) -> None:
        # Login first
        self.leo_api.init_login_synchorizer()
        token_issue_time, token = self.captcha_helper.issue_new_token(
            with_username=False)
        self.leo_api.login(token)

    @auto_retry
    def book(self) -> None:
        self.leo_api.init_booking_synchorizer()
        token = self.captcha_helper.get_token()
        self.leo_api.book(token, self.date, self.seat,
                          self.start_time, self.end_time)

    def run(self) -> None:
        try:
            self.login()
            # Fire up captcha helper
            self.captcha_helper.start()
            # Wait for the seat available to book
            current_time = datetime.now()
            expected_time = datetime.now().replace(
                hour=7, minute=0, second=0, microsecond=0)
            interval = expected_time - current_time
            if interval.total_seconds() > 0:
                sleep(interval.total_seconds())
            # Start booking
            self.book()
            logging.info(
                f"Seat booking success for user {self.leo_api.username}")
        except Exception as e:
            logging.warning(
                f"Seat booking failed for user {self.leo_api.username}, {e}")
