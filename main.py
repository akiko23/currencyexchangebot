import math
import time

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, \
    ReplyKeyboardRemove
from aiogram.utils import executor

from config import dp, bot, db, text_on_start, keyb_on_start, cg
from functions import get_btc_sum, request_time_left
from states import GetPaymentData, GetDataForPay, SendReview


def is_created_request(user_id):
    return int(db.get_user_attr(user_id, "request_time")) - time.time() >= 0


@dp.message_handler(commands=['start'])
async def main(message: types.Message):
    if not db.user_exists(message.from_user.id):
        db.add_user(message.from_user.id)
        await bot.send_message(message.chat.id, text_on_start, reply_markup=keyb_on_start)
    else:
        if is_created_request(message.from_user.id):
            await bot.send_message(message.from_user.id,
                                   f"До конца заявки: {request_time_left(message.from_user.id)}\n{text_on_start}",
                                   reply_markup=keyb_on_start)
        else:
            await bot.send_message(message.from_user.id, text_on_start, reply_markup=keyb_on_start)


@dp.message_handler(content_types=['text'])
async def get_message_text_commands(msg: types.Message):
    user_id = msg.from_user.id
    if msg.text == "Купить":
        try:
            created_request = is_created_request(user_id)
        except:
            created_request = False
        if not created_request:
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
        else:
            await bot.send_message(msg.from_user.id,
                                   f"Вы не можете делать больше одной заявки. Пожалуйста, подождите, пока админ рассмотрит текущую, или еще {request_time_left(msg.from_user.id)}")

    elif msg.text == "Оставить отзыв":
        await bot.delete_message(msg.from_user.id, msg.message_id)
        await bot.send_message(msg.from_user.id, "Пожалуйста, напишите ваш отзыв о боте")
        await SendReview.get_review.set()

    elif msg.text in ("Назад", "Отмена", "В меню"):
        await bot.send_message(user_id, text_on_start, reply_markup=keyb_on_start)

    else:
        await bot.send_message(user_id, "***", reply_markup=keyb_on_start)


@dp.message_handler(content_types=['text'], state=SendReview.get_review)
async def send_review(msg: types.Message, state: FSMContext):
    review = msg.text
    await bot.delete_message(message_id=msg.message_id, chat_id=msg.from_user.id)
    await bot.send_message(msg.from_user.id, f"Большое спасибо за отзыв\n"
                                             f"Можете и дальше продолжать пользоваться ботом!",
                           reply_markup=keyb_on_start)
    await state.finish()
    await bot.send_message(781873536, f'@{msg.from_user.username} оставил отзыв:\n'
                                      f'"{review}"')


@dp.message_handler(content_types=['text'], state=GetPaymentData.get_currency)
async def get_currency(msg: types.Message, state: FSMContext):
    user_id = msg.from_user.id
    if msg.text == "BTC":
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

    elif msg.text == "ETH":
        await state.finish()
        await bot.send_message(user_id, "скоро...", reply_markup=keyb_on_start)
    elif msg.text == "Назад":
        await state.finish()
        await bot.send_message(user_id, "Операция отменена, вы возвращены в главное меню",
                               reply_markup=keyb_on_start)


@dp.message_handler(content_types=['text'], state=GetPaymentData.get_payment)
async def get_payment(msg: types.Message, state: FSMContext):
    user_id = msg.from_user.id
    sd = ReplyKeyboardRemove()

    await bot.send_message(user_id, "1", reply_markup=sd)
    await bot.delete_message(user_id, msg.message_id + 1)
    
    currency_keyb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="BTC", callback_data="enter_amount-btc"),
                    InlineKeyboardButton(text="Рубль", callback_data="enter_amount-rub")
                ]
            ],
    )
    if msg.text == "Сбербанк":
        db.set_user_attr(user_id, "bank", "sberbank")
        await bot.send_message(user_id, "Выберите как вам удобно ввести сумму:", reply_markup=currency_keyb)
        await state.finish()
    elif msg.text == "Тинькофф":
        db.set_user_attr(user_id, "bank", "tinkoff")
        await bot.send_message(user_id, "Выберите как вам удобно ввести сумму:", reply_markup=currency_keyb)
        await state.finish()
    elif msg.text == "Отмена":
        await state.finish()
        await bot.send_message(user_id, "Операция отменена, вы возвращены в главное меню",
                               reply_markup=keyb_on_start)


@dp.callback_query_handler(Text(startswith="enter_amount"))
async def process_enter_amount(call: types.CallbackQuery):
    currency = call.data.split('-')[1]
    price = cg.get_price(ids='bitcoin', vs_currencies='rub')["bitcoin"]["rub"]

    if currency == "btc":
        await call.message.edit_text(f"""📈 Текущий курс 1 BTC = {price * 1.123} рублей
Сколько вы хотите купить BTC?  ( Введите количество монет в формате X.ХХХХ - Пример:  0.011  )""",
                                     reply_markup=InlineKeyboardMarkup(
                                         inline_keyboard=[
                                             [InlineKeyboardButton(text="Отмена",
                                                                   callback_data="cancel_paymentprocess")]
                                         ]
                                     ))
        await GetDataForPay.get_btc_amount.set()
    elif currency == "rub":
        await call.message.edit_text(f"""📈 Текущий курс 1 BTC = {price * 1.123}
Сколько вы хотите купить, введите корректную сумму? (Пример - 3500)""", reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Отмена", callback_data="cancel_paymentprocess")]
            ]
        ))
        await GetDataForPay.get_rub_amount.set()


@dp.message_handler(content_types=['text'], state=GetDataForPay.get_btc_amount)
async def get_btc_amount(msg: types.Message):
    user_id = msg.from_user.id
    try:
        amount = float(msg.text)
        price = cg.get_price(ids='bitcoin', vs_currencies='rub')["bitcoin"]["rub"]

        await bot.delete_message(user_id, msg.message_id - 1)
        rub_price = amount * price
        if rub_price >= 2500:
            db.set_user_attr(user_id, column_name="amount", value=amount)
            db.set_user_attr(user_id, column_name="currency", value="btc")

            await bot.send_message(user_id, "Введите адрес для получения.", reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Отмена", callback_data="cancel_paymentprocess")]
                ]
            ))
            await GetDataForPay.get_crypto_pocket.set()
        else:
            await bot.send_message(user_id, "Введенная сумма не может быть меньше 2500 рублей!",
                                   reply_markup=InlineKeyboardMarkup(
                                       inline_keyboard=[
                                           [InlineKeyboardButton(text="Отмена", callback_data="cancel_paymentprocess")]
                                       ]
                                   ))
    except ValueError:
        await bot.send_message(user_id, "Вы некорректно ввели данные", reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Отмена", callback_data="cancel_paymentprocess")]
            ]
        ))


@dp.message_handler(content_types=['text'], state=GetDataForPay.get_rub_amount)
async def get_btc_amount(msg: types.Message):
    user_id = msg.from_user.id
    try:
        amount = float(msg.text)
        if amount >= 2500:
            db.set_user_attr(user_id, column_name="amount", value=amount)
            db.set_user_attr(user_id, column_name="currency", value="rub")

            try:
                await bot.delete_message(user_id, msg.message_id - 1)
            except:
                pass
            await bot.send_message(user_id, "Введите адрес для получения.", reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Отмена", callback_data="cancel_paymentprocess")]
                ]
            ))
            await GetDataForPay.get_crypto_pocket.set()
        else:
            await bot.send_message(user_id, "Введенная сумма не может быть меньше 2500 рублей!",
                                   reply_markup=InlineKeyboardMarkup(
                                       inline_keyboard=[
                                           [InlineKeyboardButton(text="Отмена", callback_data="cancel_paymentprocess")]
                                       ]
                                   ))
    except ValueError:
        await bot.send_message(user_id, "Вы некорректно ввели данные", reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Отмена", callback_data="cancel_paymentprocess")]
            ]
        ))


@dp.message_handler(content_types=['text'], state=GetDataForPay.get_crypto_pocket)
async def get_crypto_pocket(msg: types.Message, state: FSMContext):
    if 23 <= len(msg.text) <= 65:
        db.set_user_attr(msg.from_user.id, "pocket_address", msg.text)
        sum_in_btc = get_btc_sum(msg.from_user.id)

        await bot.delete_message(msg.from_user.id, msg.message_id - 1)
        await bot.send_message(msg.from_user.id, f"""⚠️ Внимание ⚠️ 
Проверьте правильно ли вы указали адрес и количество BTC
    
📎  К получению ➖   {round(sum_in_btc, 6)} BTC.
📎  Проверьте адрес ➖   {db.get_user_attr(msg.from_user.id, "pocket_address")}
🔴 ОЧЕНЬ ВАЖНО 🔴""", reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Всё указано верно", callback_data="payments_correct")],
                [InlineKeyboardButton(text="Отмена операции", callback_data="cancel_paymentprocess")]
            ]
        ))
        await state.finish()
    else:
        await bot.send_message(msg.from_user.id,
                               "Вы некорректно ввели адрес кошелька(его длина должна составлять не менее 23 и не более 65 символов)",
                               reply_markup=InlineKeyboardMarkup(
                                   inline_keyboard=[
                                       [InlineKeyboardButton(text="Отмена операции",
                                                             callback_data="cancel_paymentprocess")]
                                   ]
                               ))


@dp.callback_query_handler(Text(startswith="payments_correct"))
async def process_payments1(call: types.CallbackQuery):
    price = cg.get_price(ids='bitcoin', vs_currencies='rub')["bitcoin"]["rub"]

    card_numbers = {
        "sberbank": "5469 9804 2082 3664",
        "tinkoff": "2200 7004 8778 3085"
    }
    bank = db.get_user_attr(call.from_user.id, "bank")
    card_num = card_numbers[bank]

    summ_in_rub = db.get_user_attr(call.from_user.id, "amount")
    if db.get_user_attr(call.from_user.id, "currency") == "btc":
        summ_in_rub = math.ceil(price * db.get_user_attr(call.from_user.id, "amount") * 1.123)

    summ = get_btc_sum(call.from_user.id)
    await call.message.edit_text(f"""⚠️  Ваша заявка действует ➡️ 30 ⬅️ минут  ⏰
    
📎  Карта {bank[0].upper() + bank[1:]} RUB  ➖  `{card_num}`
📎  Сумма ➖    {summ_in_rub} RUB
📎  К получению ➖  {round(summ, 6)} BTC.
📎  Проверьте адрес ➖   {db.get_user_attr(call.from_user.id, "pocket_address")}
🔴 ОЧЕНЬ ВАЖНО 🔴

Вводите точную сумму  как выдал☝️ вам БОТ❗️
Комментарий указывать  не нужно❗️
▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️
🔆 Если вдруг у вас возникли трудности или вам что то не понятно, напишите Оператору или
📍Тех.поддержка @SirSwapper 👨‍💻Оператор/Администратор @MisterSwapper""", reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Оплатил", callback_data=f"true_payed")],
            [InlineKeyboardButton(text="Отмена операции", callback_data="stop_pay_process")]
        ]
    ), parse_mode="MARKDOWN")


@dp.callback_query_handler(Text(startswith="true_payed"))
async def process_payments2(call: types.CallbackQuery):
    currency = db.get_user_attr(call.from_user.id, "currency")
    price = cg.get_price(ids='bitcoin', vs_currencies='rub')["bitcoin"]["rub"]

    btc_amount = db.get_user_attr(call.from_user.id, "amount") if currency == "btc" else db.get_user_attr(
        call.from_user.id, "amount") / (price * 1.123)
    print(btc_amount)

    db.set_user_attr(call.from_user.id, "request_time", int(time.time()) + 1800)

    await bot.delete_message(call.from_user.id, call.message.message_id)
    await bot.send_message(call.from_user.id, text=f"""Ваша заявка была создана.
Номер: {db.get_user_attr(call.from_user.id, "id")} 
Время: 30 минут 
Спасибо за использование нашего обмен бота SWAPPER""", reply_markup=keyb_on_start)

    await bot.send_message(781873536, f"""Номер заявки: {db.get_user_attr(call.from_user.id, "id")}
Сумма обмена: {math.ceil(btc_amount * price)} RUB
Сумма к получению: {round(btc_amount, 6)} BTC.
На кошелек: {db.get_user_attr(call.from_user.id, "pocket_address")}

Время заявки: {request_time_left(call.from_user.id)}""", reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Завершить заявку", callback_data=f"finish_request-{call.from_user.id}")]
        ]
    ))


@dp.callback_query_handler(Text(startswith="finish_request"))
async def finish_request(call: types.CallbackQuery):
    user_id = call.data.split('-')[1]
    db.set_user_attr(user_id, "request_time", 0)

    await bot.send_message(user_id, "Ваша заявка была завешена, теперь вы можете создать новую!")


@dp.callback_query_handler(Text("cancel_paymentprocess"), state=GetDataForPay.all_states)
@dp.callback_query_handler(Text("cancel_paymentprocess"))
async def cancel_payment_process(call: types.CallbackQuery, state: FSMContext):
    await state.finish()

    try:
        await bot.delete_message(call.from_user.id, call.message.message_id)
    except:
        pass
    await bot.send_message(call.from_user.id, f"Вы отменили процесс покупки\n\n{text_on_start}",
                           reply_markup=keyb_on_start)


@dp.callback_query_handler(Text("stop_pay_process"))
async def stop_pay_process(call: types.CallbackQuery):
    await bot.delete_message(call.from_user.id, call.message.message_id)
    await bot.send_message(call.from_user.id, f"Вы отменили процесс покупки\n\n{text_on_start}",
                           reply_markup=keyb_on_start)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
