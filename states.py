from aiogram.fsm.state import State, StatesGroup


class CreateMailing(StatesGroup):
    photo = State()
    text = State()


class SendMessage(StatesGroup):
    user_id = State()
    text = State()
    buts = State()
    count = State()
    but_text = State()
    but_url = State()
    photo = State()
    category = State()
    commit = State()


class GetPhotoMenu(StatesGroup):
    file_id = State()


class CreateRaffle(StatesGroup):
    photo = State()
    name = State()
    description = State()
    winners_count = State()
    end_time = State()
    preview = State()