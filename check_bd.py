import asyncio
import time

from config import db, bot, keyb_on_start


async def check_requested_users():
    while True:
        requested_users = db.get_users_with_request()
        for user_id in requested_users:
            request_end_time = db.get_user_attr(user_id, "request_time")
            if int(time.time()) - request_end_time >= 0:
                print(user_id)
                db.set_user_attr(user_id, "request_time", 0)
                await bot.send_message(user_id, """🚫Оплата не поступила🚫 

Ваш резерв отменен автоматически. Средства переведенные после окончания резерва возврату не подлежат❗""", reply_markup=keyb_on_start)
        time.sleep(4)


def check_bd():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(check_requested_users())
    loop.close()


if __name__ == '__main__':
    check_bd()
