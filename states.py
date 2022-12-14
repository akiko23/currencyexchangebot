from aiogram.dispatcher.filters.state import StatesGroup, State


class GetPaymentData(StatesGroup):
    get_currency = State()
    get_payment = State()


class PayProcess(StatesGroup):
    get_btc_amount = State()
    get_rub_amount = State()
    get_crypto_pocket = State()
