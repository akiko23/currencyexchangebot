import datetime
import time

from config import db, cg


def get_btc_sum(user_id):
    currency = db.get_user_attr(user_id, "currency")
    price = cg.get_price(ids='bitcoin', vs_currencies='rub')["bitcoin"]["rub"]

    if currency == "btc":
        sum_in_btc = db.get_user_attr(user_id, "amount")
    else:
        sum_in_btc = float(db.get_user_attr(user_id, "amount")) / (price * 1.123)

    return sum_in_btc


def request_time_left(user_id):
    request_time = db.get_user_attr(user_id, "request_time")
    time_now = int(time.time())

    middle_time = int(request_time) - time_now
    return str(datetime.timedelta(seconds=middle_time))[2:]
