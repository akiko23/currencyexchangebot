from aiogram.dispatcher.filters.state import StatesGroup, State


class GetPaymentData(StatesGroup):
    get_currency = State()
    get_payment = State()


class GetDataForPay(StatesGroup):
    get_btc_amount = State()
    get_rub_amount = State()
    get_crypto_pocket = State()


class SendReview(StatesGroup):
    get_review = State()

# class ProcessPay(StatesGroup):

