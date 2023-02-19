from aiogram import Dispatcher, Bot
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from pycoingecko import CoinGeckoAPI

import os
from db import Database

cg = CoinGeckoAPI()
db = Database("dbase")

bot = Bot(os.environ.get('BOT+TOKEN'))
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

