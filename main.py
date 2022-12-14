from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, \
    ReplyKeyboardRemove
from aiogram.utils import executor
from pycoingecko import CoinGeckoAPI

from db import Database
from states import GetPaymentData, PayProcess

cg = CoinGeckoAPI()
db = Database("dbase")

bot = Bot('5819253858:AAH_ZxMh6O2BXON3K0nWt7CIgXmyl_SkIoQ')
dp = Dispatcher(bot, storage=MemoryStorage())

text_on_start = """Приветствуем вас, дорогие друзья!!!

Вы соглашаетесь с правилами нашего сервиса, как только нажали кнопку
💡/Start 
❌Ошибка в вашем платеже рассматриваться не будет!!!
⛔️Средства возврату не подлежат!!!
Будьте внимательны при вводе данных и все получится ✅✅✅
САМЫЙ НИЗКИЙ КУРС, просто сравни 📊
КОМИССИЯ =  0
Моментальный бот
Время работы: 24/7👍👍👍

По вопросам сотрудничества Оператор/Администратор @MisterSwapper
Тех.поддержка @SirSwapper
Чат/отзывы
@SwapperReview"""

keyb_on_start = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Купить"),
            KeyboardButton(text="Продать")
        ],
        [
            KeyboardButton(text="О нас❓"),
            KeyboardButton(text="Как совершить обмен❓")
        ],
        [
            KeyboardButton(text="Оставить отзыв"),
            KeyboardButton(text="Реферальная ссылка")
        ]
    ],
    resize_keyboard=True,
    row_width=2
)


@dp.message_handler(commands=['start'])
async def main(message: types.Message):
    db.add_user(message.from_user.id) if not db.user_exists(message.from_user.id) else None
    await bot.send_message(message.chat.id, text_on_start, reply_markup=keyb_on_start)


@dp.message_handler(content_types=['text'])
async def get_message_text_commands(msg: types.Message):
    user_id = msg.from_user.id
    match msg.text:
        case "Купить":
            await bot.send_message(user_id, "Выберите что хотите купить.", reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [
                        KeyboardButton("BTC"),
                        KeyboardButton("ETH")
                    ],
                    [KeyboardButton("Назад")]
                ],
                resize_keyboard=True,
                row_width=2
            ))
            await GetPaymentData.get_currency.set()
        case "Назад" | "Отмена" | "В меню":
            await bot.send_message(user_id, text_on_start, reply_markup=keyb_on_start)

        case _:
            await bot.send_message(user_id, text_on_start, reply_markup=keyb_on_start)


@dp.message_handler(content_types=['text'], state=GetPaymentData.get_currency)
async def get_currency(msg: types.Message, state: FSMContext):
    user_id = msg.from_user.id
    match msg.text:
        case "BTC":
            await bot.send_message(user_id, "Выберите способ оплаты:", reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [
                        KeyboardButton("Сбербанк"),
                        KeyboardButton("Тинькофф"),
                    ],
                    [KeyboardButton("Отмена")]
                ],
                resize_keyboard=True,
                row_width=2
            ))
            await GetPaymentData.get_payment.set()

        case "ETH":
            await bot.send_message(user_id, "скоро...", reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton("В меню")]
                ],
                resize_keyboard=True,
                row_width=2
            ))
        case "Отмена":
            await state.finish()
            await bot.send_message(user_id, "Операция отменена, вы возвращены в главное меню",
                                   reply_markup=keyb_on_start)


@dp.message_handler(content_types=['text'], state=GetPaymentData.get_payment)
async def get_payment(msg: types.Message, state: FSMContext):
    user_id = msg.from_user.id
    match msg.text:
        case "Сбербанк":
            sd = ReplyKeyboardRemove()

            await bot.send_message(user_id, "1", reply_markup=sd)
            await bot.delete_message(user_id, msg.message_id + 1)

            await bot.send_message(user_id, "Выберите как вам удобно ввести сумму:", reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="BTC", callback_data="enter_amount-btc"),
                        InlineKeyboardButton(text="Рубль", callback_data="enter_amount-btc")
                    ]
                ],
            ))
            await state.finish()
        case "Тинькофф":
            pass
        case "Отмена":
            await state.finish()
            await bot.send_message(user_id, "Операция отменена, вы возвращены в главное меню",
                                   reply_markup=keyb_on_start)


@dp.callback_query_handler(Text(startswith="enter_amount"))
async def process_enter_amount(call: types.CallbackQuery):
    currency = call.data.split('-')[1]
    price = cg.get_price(ids='bitcoin', vs_currencies='rub')["bitcoin"]["rub"]

    match currency:
        case "btc":
            await call.message.edit_text(f"""📈 Текущий курс 1 BTC = {price} рублей
Сколько вы хотите купить BTC?  ( Введите количество монет в формате X.ХХХХ - Пример:  0.011  )""",
                                         reply_markup=InlineKeyboardMarkup(
                                             inline_keyboard=[
                                                 [InlineKeyboardButton(text="Отмена",
                                                                       callback_data="cancel_paymentprocess")]
                                             ]
                                         ))
            await PayProcess.get_btc_amount.set()
        case "Рубль":
            await call.message.edit_text(f"""📈 Текущий курс 1 BTC = {price}
Сколько вы хотите купить, введите корректную сумму? (Пример - 3500)""", reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Отмена", callback_data="cancel_paymentprocess")]
                ]
            ))
            await PayProcess.get_rub_amount.set()


@dp.message_handler(content_types=['text'], state=PayProcess.get_btc_amount)
async def get_btc_amount(msg: types.Message):
    user_id = msg.from_user.id
    try:
        amount = float(msg.text)
        db.set_user_attr(user_id, column_name="amount", value=amount)
        db.set_user_attr(user_id, column_name="currency", value="btc")

        await bot.delete_message(user_id, msg.message_id - 1)
        await bot.send_message(user_id, "Введите адрес для получения.", reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Отмена", callback_data="cancel_paymentprocess")]
            ]
        ))
        await PayProcess.get_crypto_pocket.set()
    except Exception as e:
        print(e)
        await bot.send_message(user_id, "Вы некорректно ввели данные", reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Отмена", callback_data="cancel_paymentprocess")]
            ]
        ))


@dp.message_handler(content_types=['text'], state=PayProcess.get_crypto_pocket)
async def get_crypto_pocket(msg: types.Message):
    db.set_user_attr(msg.from_user.id, "pocket_address", msg.text)

    await bot.delete_message(msg.from_user.id, msg.message_id - 1)
    await bot.send_message(msg.from_user.id, """⚠️ Внимание ⚠️ 
Проверьте правильно ли вы указали адрес и количество BTC

📎  К получению ➖   Сумма указанная в рублях если человек писал в Рублях или же сумма в  BTC.
📎  Проверьте адрес ➖   bc1qdqhhqtu5wvpf7rya84ee0drwyex74gcnfdfvtk(адресс котороый пользователь ввёл)
🔴 ОЧЕНЬ ВАЖНО 🔴""", reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Всё указано верно", callback_data="pay_process-data_correct")],
            [InlineKeyboardButton(text="Отмена операции", callback_data="cancel_paymentprocess")]
        ]
    ))


@dp.callback_query_handler(Text("cancel_paymentprocess"), state=PayProcess.all_states)
async def stop_pay_process(call: types.CallbackQuery, state: FSMContext):
    await state.finish()

    await bot.delete_message(call.from_user.id, call.message.message_id)
    await bot.send_message(call.from_user.id, f"Вы отменили процесс покупки\n\n{text_on_start}",
                           reply_markup=keyb_on_start)


# def sberbankbitcoin(message):
#     button = types.ReplyKeyboardRemove()
#     price = cg.get_price(ids='bitcoin', vs_currencies='rub')
#     msg = bot.send_message(message.chat.id,
#                            f'1 bitcoin == {price["bitcoin"]["rub"] * 1.13} RUB\nМинимальная сумма обмена'
#                            f' состовляет 2000 рублей.\nПожалуйста, введите сумму вашего обмена.', reply_markup=button)
#
#     bot.register_next_step_handler(msg, proverka)


# def proverka(message):
#     try:
#         global course
#         course = {}
#         proverka = {}
#         proverka["sberbankbitcoin"] = message.text
#         course = float(proverka["sberbankbitcoin"])
#         price = cg.get_price(ids='bitcoin', vs_currencies='rub')
#
#         if course >= 2000:
#             msg = bot.send_message(message.chat.id,
#                                    f'Вы получите {course / (price["bitcoin"]["rub"] * 1.13)} BTC на ваш кошелек.\n'
#                                    f'Пожалуйста, укажите ваш BTC адрес')
#             bot.register_next_step_handler(msg, proverka2)
#
#         else:
#             bot.send_message(message.chat.id, 'Минимальная сумма обмена состовляет 2000 рублей')
#             sberbankbitcoin(message)
#     except ValueError:
#         bot.send_message(message.chat.id, 'Пожалуйста введите корректную сумму')
#         sberbankbitcoin(message)
#
#
# def proverka2(message):
#     global wallet
#     wallet = {}
#     wallet["proverka"] = message.text
#     button = ReplyKeyboardMarkup(resize_keyboard=True)
#     button.add(KeyboardButton('Подтверждаю оплату'))
#
#     price = cg.get_price(ids='bitcoin', vs_currencies='rub')
#     msg = bot.send_message(message.chat.id,
#                            f'Вы обмениваете {course} RUB на {course / (price["bitcoin"]["rub"] * 1.13)} BTC.\n'
#                            f'Ваш кошелек: {wallet["proverka"]}\n\n'
#                            f'Мы ожидаем перевод денежных средств на Tinkoff в размере {course} RUB по номеру карты: **** **** **** ****',
#                            reply_markup=button)
#
#     bot.register_next_step_handler(msg, finish)
#
#
# def finish(message):
#     price = cg.get_price(ids='bitcoin', vs_currencies='rub')
#     if message.text == 'Подтверждаю оплату':
#         bot.send_message(message.chat.id,
#                          f'Ваша заявка была создана {datetime.datetime.now()}. Обмен происходит обычно в течении 30минут.\n'
#                          'Спасибо за использование нашего обмен бота SWAPPER')
#         bot.send_message(f"Сумма обмена: {course}\n"
#                          f"Сумма к получению: {course / (price['bitcoin']['rub'] * 1.13)} BTC\n"
#                          f"На кошелек: {wallet['proverka']}\n\n"
#                          f"Время заявки: {datetime.datetime.now()}")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
