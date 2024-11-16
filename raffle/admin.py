from datetime import datetime

from aiogram import F
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ContentType, Message
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.widgets.input import MessageInput, TextInput
from aiogram_dialog.widgets.kbd import SwitchTo, Next, Button
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from db_tools import get_raffles_by_status, db_create_raffle
from tools import process_raffle
from keyboards import raffle_menu, admin_raffle_menu
from states import CreateRaffle

router = Router()
FINISHED_KEY = "finished"
CANCEL_EDIT = SwitchTo(
    Const("Отменить редактирование"),
    when=F["dialog_data"][FINISHED_KEY],
    id="cnl_edt",
    state=CreateRaffle.preview
)


@router.callback_query(F.data == "admin_raffle")
async def func(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Выберите тип", reply_markup=admin_raffle_menu())
    await call.answer()


@router.callback_query(F.data.startswith("admin_raffle_status:"))
async def func(call: CallbackQuery, state: FSMContext):
    raffle_type = call.data.split(":")[1]
    raffles = get_raffles_by_status(raffle_type)
    await call.message.answer("Меню розыгрышей", reply_markup=raffle_menu(for_admin=True))
    await call.answer()


@router.callback_query(F.data == "create_raffle")
async def func(call: CallbackQuery, state: FSMContext, dialog_manager: DialogManager):
    await dialog_manager.start(CreateRaffle.photo)
    await call.answer()


async def next_or_end(event, widget, dialog_manager: DialogManager, *_):
    if dialog_manager.dialog_data.get(FINISHED_KEY):
        await dialog_manager.switch_to(CreateRaffle.preview)
    else:
        await dialog_manager.next()


def winner_count_check(text: str) -> str:
    if all(ch.isdigit() for ch in text) and 0 < int(text):
        return text
    raise ValueError


def end_time_check(text: str) -> str:
    try:
        my_datetime = datetime.strptime(text, "%d.%m.%Y %H:%M")
        if my_datetime < datetime.now():
            raise ValueError
    except ValueError:
        raise ValueError
    return text


async def save_photo(message: Message, widget, dialog_manager: DialogManager):
    dialog_manager.dialog_data["photo"] = message.photo[-1].file_id
    await next_or_end(message, widget, dialog_manager)


async def save_description(message: Message, widget, dialog_manager: DialogManager, text):
    dialog_manager.dialog_data["description"] = message.html_text
    print(message.html_text)
    await next_or_end(message, widget, dialog_manager)


def get_raffle_data(dialog_manager: DialogManager):
    return {
        "photo": dialog_manager.dialog_data["photo"],
        "name": dialog_manager.find("name").get_value(),
        "description": dialog_manager.dialog_data["description"],
        "winners_count": dialog_manager.find("winners_count").get_value(),
        "end_time": dialog_manager.find("end_time").get_value(),
    }


async def preview_getter(dialog_manager: DialogManager, **kwargs):
    dialog_manager.dialog_data[FINISHED_KEY] = True
    raffle_data = get_raffle_data(dialog_manager)
    text = f'{raffle_data["name"]}\n' \
           f'{raffle_data["description"]}\n\n' \
           f'Количество победителей: {raffle_data["winners_count"]}\n' \
           f'Время окончания: {raffle_data["end_time"]}\n'

    return {
        "photo": MediaAttachment(ContentType.PHOTO, file_id=MediaId(dialog_manager.dialog_data["photo"])),
        "text": text
    }


async def create_raffle(event, widget, dialog_manager: DialogManager):
    raffle_data = get_raffle_data(dialog_manager)
    raffle_id = db_create_raffle(raffle_data)
    print("VJQ", raffle_id)
    scheduler: AsyncIOScheduler = dialog_manager.middleware_data["scheduler"]
    run_date = datetime.strptime(raffle_data["end_time"], "%d.%m.%Y %H:%M")
    scheduler.add_job(process_raffle, "date", run_date=run_date, args=(raffle_id,))

    await dialog_manager.done()
    await event.message.answer("Розыгрыш создан!")


create_raffle_dialog = Dialog(
    Window(
        Const("Пришлите фото!"),
        MessageInput(
            func=save_photo,
            content_types=ContentType.PHOTO,
        ),
        CANCEL_EDIT,
        state=CreateRaffle.photo,
    ),
    Window(
        Const("Введите короткое название розыгрыша"),
        TextInput(id="name", on_success=next_or_end),
        CANCEL_EDIT,
        state=CreateRaffle.name,
    ),
    Window(
        Const("Пришлите описание розыгрыша"),
        TextInput(id="description", on_success=save_description),
        CANCEL_EDIT,
        state=CreateRaffle.description,
    ),
    Window(
        Const("Введите количество победителей"),
        TextInput(id="winners_count", type_factory=winner_count_check, on_success=next_or_end),
        CANCEL_EDIT,
        state=CreateRaffle.winners_count,
    ),
    Window(
        Const("Введите время окончания в формате дд.мм.гггг чч:мм (12.02.2024 12:00)\nДата больше текущей"),
        TextInput(id="end_time", type_factory=end_time_check, on_success=next_or_end),
        CANCEL_EDIT,
        state=CreateRaffle.end_time,
    ),
    Window(
        DynamicMedia("photo"),
        Format("{text}"),
        SwitchTo(
            Const("Изменить баннер"),
            state=CreateRaffle.photo,
            id="to_photo"
        ),
        SwitchTo(
            Const("Изменить название"),
            state=CreateRaffle.name,
            id="to_name"
        ),
        SwitchTo(
            Const("Изменить описание"),
            state=CreateRaffle.description,
            id="to_description"
        ),
        SwitchTo(
            Const("Изменить количество победителей"),
            state=CreateRaffle.winners_count,
            id="to_winners_count"
        ),
        SwitchTo(
            Const("Изменить время окончания"),
            state=CreateRaffle.end_time,
            id="to_end_time"
        ),
        Button(
            Const("Создать"),
            id="create",
            on_click=create_raffle,
        ),

        parse_mode="HTML",
        state=CreateRaffle.preview,
        getter=preview_getter,
    ),
)
