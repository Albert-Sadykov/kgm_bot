from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def choice_category():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Xbox", callback_data="choice_category_xbox"),
         InlineKeyboardButton(text="Steam", callback_data="choice_category_steam")],
        [InlineKeyboardButton(text="PlayStation", callback_data="choice_category_playstation")],
        [InlineKeyboardButton(text="Розыгрыши", callback_data="raffle")]])


def raffle_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Активные", callback_data="raffle_status:active")],
        [InlineKeyboardButton(text="Завершенные", callback_data="raffle_status:finish")]
    ])


def get_raffles_kb(raffles):
    return InlineKeyboardMarkup(inline_keyboard=[
        *[
            [
                InlineKeyboardButton(
                    text=raffle[2] + ("" if raffle[5] == "active" else " (Завершено)"),
                    callback_data=f"raffle:{raffle[0]}"
                )
            ] for raffle in raffles
        ]
    ])


def get_raffle_kb(raffle_id, already_participant):
    if already_participant:
        btn = InlineKeyboardButton(text="Вы уже участвуете!", callback_data=f"raffle_start:{raffle_id}")
    else:
        btn = InlineKeyboardButton(text="Участвовать!", callback_data=f"raffle_start:{raffle_id}")
    return InlineKeyboardMarkup(inline_keyboard=[
        [btn]
    ])


def admin_raffle_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Создать розыгрыш", callback_data="create_raffle")],
        [InlineKeyboardButton(text="Активные", callback_data="admin_raffle_status:active")],
        [InlineKeyboardButton(text="Завершенные", callback_data="admin_raffle_status:finish")]
    ])


def admin_panel():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Сделать рассылку", callback_data="create_mailing")],
                         [InlineKeyboardButton(text="Выгрузить базу данных", callback_data="upload_db")],
                         [InlineKeyboardButton(text="Отправить сообщение", callback_data="send_message")],
                         [InlineKeyboardButton(text="Установить фото меню", callback_data="set_menu")],
                         [InlineKeyboardButton(text="Розыгрыши", callback_data="admin_raffle")]]
    )

    return kb


def choice_parse():
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Xbox", callback_data="parse_xbox"),
                                                InlineKeyboardButton(text="Steam", callback_data="parse_steam")], [
                                                   InlineKeyboardButton(text="PlayStation",
                                                                        callback_data="parse_playstation")]])

    return kb


def commit_send_msg():
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Отправить сообщение!")],
                                       [KeyboardButton(text="Отмена")]])

    return kb


def create_url_buttons(texts, urls):
    kb = []

    for text, url in zip(texts, urls):
        kb.append([InlineKeyboardButton(text=text, url=url)])

    if len(kb) != 0:
        return InlineKeyboardMarkup(inline_keyboard=kb)

    return None


def miss():
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Пропустить")]])
    return kb


def choice_category_to_send():
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Xbox"), KeyboardButton(text="Steam")], [KeyboardButton(text="PlayStation")]])
    return kb


def choice_menu_set_photo():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Xbox", callback_data="set_photo_menu_xbox")],
                         [InlineKeyboardButton(text="PlayStation", callback_data="set_photo_menu_playstation")],
                         [InlineKeyboardButton(text="Steam", callback_data="set_photo_menu_steam")],
                         [InlineKeyboardButton(text="Xbox/PlayStation",
                                               callback_data="set_photo_menu_playstation_xbox")],
                         [InlineKeyboardButton(text="Xbox/Steam", callback_data="set_photo_menu_steam_xbox")],
                         [InlineKeyboardButton(text="PlayStation/Steam",
                                               callback_data="set_photo_menu_playstation_steam")],
                         [InlineKeyboardButton(text="PlayStation/Steam/Xbox",
                                               callback_data="set_photo_menu_playstation_steam_xbox")]]
    )
    return kb
