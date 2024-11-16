import asyncio
import logging

from aiogram.enums import ContentType
from aiogram_dialog import setup_dialogs
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import raffle
from tools import send_menu, process_raffle
from aiogram import Bot, Dispatcher, types
from aiogram import F
from aiogram.filters import ChatMemberUpdatedFilter, MEMBER, LEFT
from aiogram.filters.command import Command
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from config import BOT_API_KEY, CHANNEL_ID, ADMINS_IDS, PHOTO_ID
from keyboards import choice_category
from db_tools import create_user, user_exist, set_is_signed, add_category, delete_category, get_categories_str, \
    categories_exist, get_has_key, update_has_key
import admin_panel

from promocode import update_sheet

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_API_KEY)
dp = Dispatcher()


# @dp.message(F.content_type == ContentType.PHOTO)
# async def photo(message: types.Message):
#     file_id = message.photo[-1].file_id
#     print(file_id)


@dp.message(Command("start"))
async def start(message: types.Message):
    if message.from_user.id in ADMINS_IDS:
        await message.answer("Вызвать админ панель: /panel")
        # return

    if not user_exist(message.from_user.id):
        user_channel_status = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=message.from_user.id)
        if user_channel_status.status.value != 'left':
            promo = update_sheet()
            await bot.send_photo(chat_id=message.chat.id, photo=PHOTO_ID,
                                 caption=f"Приветствуем в пристанище игровых подгонов и ништяков. \n\nДля начала давай выберем интересующую тебя платформу (от одной до трех) \n Ваш персональный промокод {promo}",
                                 reply_markup=choice_category())

        else:
            await bot.send_photo(chat_id=message.chat.id, photo=PHOTO_ID,
                                 caption="Вы не подписаны на наш канал @korobok_store, подпишитесь")

    else:
        if not(get_has_key(message.from_user.id)):
            update_has_key(message.from_user.id)
            promo = update_sheet()
            await bot.send_photo(chat_id=message.chat.id, photo=PHOTO_ID,
                                caption=f"Приветствуем в пристанище игровых подгонов и ништяков. \n\nДля начала давай выберем интересующую тебя платформу (от одной до трех) \n Ваш персональный промокод {promo} ",
                                reply_markup=choice_category())
        else:
            await bot.send_photo(chat_id=message.chat.id, photo=PHOTO_ID,
                                caption=f"Приветствуем в пристанище игровых подгонов и ништяков. \n\nДля начала давай выберем интересующую тебя платформу (от одной до трех)",
                                reply_markup=choice_category())


@dp.callback_query(F.data.startswith('choice_category_'))
async def registrate_user(call: types.CallbackQuery):
    uid = call.from_user.id
    category = call.data.replace('choice_category_', '')
    try:
        if not user_exist(uid):
            create_user(uid, call.from_user.username, call.from_user.first_name, category)
            await send_menu(bot=bot, chat_id=call.from_user.id,
                            text=f"Успех, теперь ты будешь получать рассылку на тему: {get_categories_str(uid)}\n\nВсегда можно поменять или добавить другую платформу — халявы много не бывает:",
                            kb=choice_category())
        else:
            is_added = add_category(uid, category)
            if is_added:
                await call.answer("Категория добавлена")
                await send_menu(bot=bot, chat_id=call.from_user.id,
                                text=f"Успех, теперь ты будешь получать рассылку на тему(ы): {get_categories_str(uid)}\n\nВсегда можно поменять или добавить другую платформу:",
                                kb=choice_category())
            else:
                delete_category(uid, category)
                await call.answer("Категория удалена")

                if categories_exist(uid):
                    await send_menu(bot=bot, chat_id=call.from_user.id,
                                    text=f"Успех, теперь ты будешь получать рассылку на тему(ы): {get_categories_str(uid)}\n\nВсегда можно поменять или добавить другую платформу:",
                                    kb=choice_category())
                else:
                    await call.message.answer("Ты не выбрал ни одной категории, выбери интересующую:",
                                              reply_markup=choice_category())

    except Exception as e:
        raise e
        await call.message.answer("Что-то пошло не так")


@dp.chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER))
async def on_chat_member_update(event: types.ChatMemberUpdated):
    set_is_signed(user_id=event.from_user.id, value=True)
    if event.new_chat_member.status == "member":
        user_id = event.from_user.id
        try:
            if not(get_has_key(user_id)):
                update_has_key(user_id)
                promo = update_sheet()
                await bot.get_chat(user_id)
                await bot.send_message(user_id,
                                    f"Отлично! Приветствуем в пристанище игровых подгонов и ништяков. \n\nДля начала давай выберем интересующую тебя платформу (от одной до трех) \n Ваш персональный промокод {promo}",
                                    reply_markup=choice_category())
            else:
                await bot.get_chat(user_id)
                await bot.send_message(user_id,
                                    f"Отлично! Приветствуем в пристанище игровых подгонов и ништяков. \n\nДля начала давай выберем интересующую тебя платформу (от одной до трех)",
                                    reply_markup=choice_category())
        except TelegramBadRequest:
            pass


@dp.chat_member(ChatMemberUpdatedFilter(member_status_changed=LEFT))
async def on_chat_member_update(event: types.ChatMemberUpdated):
    set_is_signed(event.from_user.id, False)
    if event.new_chat_member.status == "left":
        user_id = event.from_user.id
        try:
            await bot.get_chat(user_id)
            await bot.send_message(user_id, "Вы отписались от канала, теперь вы не будете получать рассылку")
        except (TelegramBadRequest, TelegramForbiddenError):
            pass


async def main():
    # await process_raffle(3)
    # exit()
    dp.include_router(admin_panel.router)
    dp.include_router(raffle.user_raffle_router)
    dp.include_router(raffle.admin_raffle_router)
    dp.include_router(raffle.create_raffle_dialog)
    setup_dialogs(dp)
    jobstores = {
        'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
    }
    scheduler = AsyncIOScheduler(jobstores=jobstores)
    dp["scheduler"] = scheduler
    scheduler.start()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
