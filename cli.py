from datetime import datetime, timedelta
import logging
from leo import LeoLibWeb
from util import *
from captcha import get_captcha_service
from push import get_push_service
from dotenv import load_dotenv
import os
import json
from service import Booking
from time import sleep

thread_pool = []

if __name__ == "__main__":
    users = []
    load_dotenv()

    # Initialize logging level
    logging.getLogger().setLevel(os.environ.get("LOG_LEVEL"))

    # Sleep until time to book seats
    expected_time = datetime.strptime(os.environ.get("TRIGGER_AT"), "%H:%M:%S")
    expected_time = datetime.now().replace(hour=expected_time.hour,
                                           minute=expected_time.minute, second=expected_time.second, microsecond=0)
    interval = (expected_time - datetime.now()).total_seconds()
    if interval > 0:
        logging.info(f"Sleep {interval}")
        sleep(interval)

    # Initialize captcha
    captcha_config = extract_captcha_config()
    captcha = get_captcha_service(
        os.environ.get("CAPTCHA_SERVICE"), captcha_config)

    # Initialize push
    push_config = extract_push_config()
    push = get_push_service(os.environ.get("PUSH_SERVICE"), push_config)
    # Get user database
    with open("users.json", "r") as f:
        users = json.load(f)
    for user in users:
        date_to_book = datetime.today() + timedelta(days=1)
        api = LeoLibWeb(user.get("url"), user.get(
            "username"), user.get("password"))
        end_time = user.get("end_time")
        if date_to_book.weekday() == 1:
            end_time = 720
        date_to_book_str = date_to_book.strftime("%Y-%m-%d")
        logging.info(
            f"Start booking for username={user['username']}, seat={user['seat']}, date={date_to_book_str}, time={user['start_time']}-{user['end_time']}")
        booking = Booking(api, captcha, int(os.environ.get("CAPTCHA_REFRESH_INTERVAL")), int(os.environ.get(
            "MAX_RETRY_COUNT")), user.get("seat"), date_to_book_str, user.get("start_time"), end_time)
        booking.set_push_callback(push.get_callback())
        booking.start()
        thread_pool.append(booking)

    while len(thread_pool) > 0:
        for thread in thread_pool:
            if not thread.is_alive():
                thread_pool.remove(thread)
        sleep(1)
