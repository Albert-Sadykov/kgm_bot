from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
from config import ADMINS_IDS
from keyboards import admin_panel, choice_parse, commit_send_msg, create_url_buttons, miss, choice_category_to_send, \
    choice_menu_set_photo
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ContentType
from aiogram import F
from states import SendMessage, GetPhotoMenu
from main import bot
from db_tools import upload_users, set_photo_menu
from tools import create_csv_file, CreateButs, send_messages
from uuid import uuid1
import os
import aiogram

router = Router()


@router.message(Command("id"))
async def id(message: Message):
    await message.answer(message.photo[-1].file_id)


# Вызов панели администратора
@router.message(Command("panel"))
async def panel(message: Message):
    if message.from_user.id in ADMINS_IDS:
        await message.answer("Список инструментов:", reply_markup=admin_panel())
    else:
        await message.answer("Вы не администратор")


@router.callback_query(F.data == "set_menu")
async def choice_set_menu(call: CallbackQuery):
    await call.message.answer("Выберите категорию для установки фотографии", reply_markup=choice_menu_set_photo())


@router.callback_query(F.data.startswith('set_photo_menu_'))
async def set_menu(call: CallbackQuery, state: FSMContext):
    tag = call.data.replace('set_photo_menu_', '')
    await state.update_data(tag=tag)
    await call.message.answer("Отправьте фотографию категории")
    await state.set_state(GetPhotoMenu.file_id)


@router.message(GetPhotoMenu.file_id, F.content_type == ContentType.PHOTO)
async def get_photo_menu(message: Message, state: FSMContext):
    try:
        file_id = message.photo[-1].file_id
        data = await state.get_data()
        set_photo_menu(data['tag'], file_id)
        await message.answer("Фото успешно установлено")
    except:
        await message.answer("Что-то пошло не так")
    finally:
        await message.answer("Список инструментов:", reply_markup=admin_panel())


# Отправление сообщений конкретному пользователю
@router.callback_query(F.data == "send_message")
async def send_message(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(text="Введите id того, кому хотите отправить", reply_markup=None)
    await state.set_state(SendMessage.user_id)


@router.message(SendMessage.user_id)
async def get_user_id(message: Message, state: FSMContext):
    await state.update_data(user_id=message.text)
    await message.answer("Отправьте текст сообщения")
    await state.set_state(SendMessage.text)


@router.message(SendMessage.text)
async def get_text_to_send(message: Message, state: FSMContext):
    await state.update_data(text=message.html_text, buts_writer=CreateButs())
    await message.answer("Отправьте фотографию", reply_markup=miss())
    await state.set_state(SendMessage.photo)


@router.message(SendMessage.photo, F.content_type == ContentType.PHOTO)
async def get_text_to_send(message: Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await message.answer(
        "Сколько кнопок-ссылок прикрепить к сообщению\n(введите целое число или 0, если хотите чтобы кнопок не было)")
    await state.set_state(SendMessage.buts)


@router.message(SendMessage.photo, lambda message: message.text == 'Пропустить')
async def get_text_to_send(message: Message, state: FSMContext):
    await state.update_data(photo=None)
    await message.answer("Сколько кнопок-ссылок прикрепить к сообщению (введите целое число)")
    await state.set_state(SendMessage.buts)


@router.message(SendMessage.buts)
async def get_buts(message: Message, state: FSMContext):
    try:
        await state.update_data(buts=int(message.text))
        if int(message.text) != 0 and int(message.text) > 0:
            await state.update_data(count=1)
            await message.answer("Отправьте текст кнопки 1")
            await state.set_state(SendMessage.but_text)
        else:
            data = await state.get_data()
            text = data['text']
            kb = commit_send_msg()
            if data['photo'] != None:
                await bot.send_photo(message.chat.id,
                                     caption=text, photo=data['photo'], reply_markup=kb, parse_mode="html")
            else:
                await bot.send_message(message.chat.id,
                                       text=text, reply_markup=kb, parse_mode="html")

            await state.set_state(SendMessage.commit)
    except:
        await message.answer("Введите целое число")
        await state.set_state(SendMessage.buts)


@router.message(SendMessage.but_text)
async def get_but_text(message: Message, state: FSMContext):
    data = await state.get_data()

    await state.update_data(but_text=message.text)
    await message.answer(f"Отправьте ссылку для кнопки {data['count']}")
    await state.set_state(SendMessage.but_url)


@router.message(SendMessage.but_url)
async def get_but_url(message: Message, state: FSMContext):
    data = await state.get_data()

    data['buts_writer'].handle_data(data['but_text'], message.text, download=True)
    if data['buts'] == data["count"]:
        text = f"{data['text']}\n\n" + data[
            "buts_writer"].print_data()

        if data['photo'] != None:
            await bot.send_photo(message.chat.id,
                                 caption=text, photo=data['photo'], reply_markup=commit_send_msg(), parse_mode="html")
        else:
            await bot.send_message(message.chat.id,
                                   text=text, reply_markup=commit_send_msg(), parse_mode="html")

        await state.set_state(SendMessage.commit)

    else:
        await state.update_data(count=data["count"] + 1)
        await message.answer(f"Введите текст для кнопки {data['count'] + 1}")
        await state.set_state(SendMessage.but_text)


@router.message(SendMessage.commit)
async def get_commit(message: Message, state: FSMContext):
    if message.text == "Отправить сообщение!":

        try:
            data = await state.get_data()
            if 'category' not in data.keys():
                category = None
            else:
                category = data['category']
            await send_messages(bot, data['text'], data["user_id"], data['photo'],
                                create_url_buttons(data["buts_writer"].handle_data()[0],
                                                   data["buts_writer"].handle_data()[1]), category)

            await message.answer("Сообщение отправлено")
        except:
            await message.answer("Что-то пошло не так")

        finally:
            await state.clear()
            await message.answer(text="Список инструментов:", reply_markup=admin_panel())

    elif message.text == "Отмена":
        await state.clear()
        await panel(message)


# Выгрузка базы данных
@router.callback_query(F.data == "upload_db")
async def upload_db(call: CallbackQuery):
    await call.message.edit_reply_markup(
        text="Выберете пользователей из какой категории вы хотите выгрузить из базы данных",
        reply_markup=choice_parse())


@router.callback_query(F.data.startswith('parse_'))
async def registrate_user(call: CallbackQuery):
    try:
        await call.message.delete()
    except aiogram.exceptions.TelegramBadRequest as e:
        if "message can't be deleted" in str(e):
            print("Не удалось удалить сообщение")
        else:
            raise
    category = call.data.replace('parse_', '')

    try:
        data = upload_users(category)
        filename = f'upload_files/{uuid1()}.csv'
        create_csv_file(data, filename)

        document = FSInputFile(filename)
        await bot.send_document(call.from_user.id, document)

        os.remove(filename)

    except:
        await call.message.answer("Что-то пошло не так")

    finally:
        await call.message.answer("Список инструментов:", reply_markup=admin_panel())


# Создание рассылки
@router.callback_query(F.data == "create_mailing")
async def create_mailing(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Выберите категорию", reply_markup=choice_category_to_send())
    await state.update_data(user_id=None)
    await state.set_state(SendMessage.category)


@router.message(SendMessage.category)
async def get_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text)
    await message.answer("Отправьте текст сообщения")
    await state.set_state(SendMessage.text)
