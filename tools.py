import csv
import random

from aiogram import Bot

import config
from db_tools import upload_users, get_photo_menu, get_raffle, get_raffle_participants, set_winners, set_finish_raffle
from time import sleep
from db_tools import get_is_signed


# Класс добавляющий кнопки
class CreateButs:
    def __init__(self):
        self.texts = []
        self.urls = []

    def handle_data(self, text=None, url=None, download=False):
        if download:
            if text and url is not None:
                self.texts.append(text)
                self.urls.append(url)
        else:
            return self.texts, self.urls

    def print_data(self):
        msg = ''

        for text, url in zip(self.texts, self.urls):
            msg = msg + f'Текст кнопки: {text} \nСсылка кнопки: {url}\n\n'

        return msg


def create_csv_file(data, filename):
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['id', 'username', 'name', 'category'])
        writer.writerows(data)


async def send_messages(bot, text, uid, photo, mar, category):
    if uid != None:

        if photo != None:
            await bot.send_photo(uid,
                                 caption=text, photo=photo,
                                 reply_markup=mar, parse_mode="html")
        else:
            await bot.send_message(uid,
                                   text=text,
                                   reply_markup=mar, parse_mode="html")
    else:
        if photo != None:
            for user in upload_users(category.lower()):
                sleep(0.04)
                if get_is_signed(user_id=user[0]):
                    await bot.send_photo(user[0],
                                         caption=text, photo=photo,
                                         reply_markup=mar, parse_mode="html")
        else:
            for user in upload_users(category.lower()):
                sleep(0.04)
                if get_is_signed(user_id=user[0]):
                    await bot.send_message(user[0],
                                           text=text,
                                           reply_markup=mar, parse_mode="html")


async def send_menu(bot, chat_id, text, kb):
    file_id = get_photo_menu(chat_id)
    if file_id:
        await bot.send_photo(chat_id=chat_id, photo=file_id[0], caption=text, reply_markup=kb)
    else:
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=kb)


async def process_raffle(raffle_id):
    print("ЗАПУСТИЛИ", raffle_id)
    raffle = get_raffle(raffle_id)
    db_raffle_participants = get_raffle_participants(raffle_id)
    base_raffle_participants = [user[0] for user in db_raffle_participants]
    raffle_participants = list(base_raffle_participants)
    bot = Bot(config.BOT_API_KEY)
    winners = []
    for i in range(raffle[4]):
        while base_raffle_participants:
            winner = random.choice(base_raffle_participants)
            base_raffle_participants.remove(winner)
            chat_member = await bot.get_chat_member(chat_id=config.CHANNEL_ID, user_id=winner)
            if chat_member.status in ["creator", "administrator", "member"]:
                winners.append(winner)
                break
    set_winners(raffle_id, winners)
    set_finish_raffle(raffle_id)

    for user in winners:
        await bot.send_message(user, text=f"Поздравляем, вы выиграли в розыгрыше {raffle[2]}")
    await bot.close()
