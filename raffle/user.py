from aiogram import F
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

import config
from db_tools import get_raffles_by_status, get_raffle, get_raffle_participant, create_raffle_participant, get_winners, get_raffles_for_user
from keyboards import raffle_menu, get_raffles_kb, get_raffle_kb

router = Router()


@router.callback_query(F.data == "raffle")
async def func(call: CallbackQuery, state: FSMContext):
    raffles = get_raffles_for_user()
    await call.message.answer("Выберите розыгрыш", reply_markup=get_raffles_kb(raffles))
    await call.answer()



@router.callback_query(F.data.startswith("raffle:"))
async def func(call: CallbackQuery, state: FSMContext):
    await call.answer()
    raffle_id = int(call.data.split(":")[1])
    raffle = get_raffle(raffle_id)
    if raffle[5] == "finish":
        caption = "Розыгрыш завершен\nСписок победителей:\n"
        winners = get_winners(raffle_id)
        print(winners)
        for winner in winners:
            caption += "@" + str(winner[0]) + "\n"
        return await call.message.answer_photo(
            raffle[1],
            caption=caption
        )

    raffle_participant = get_raffle_participant(raffle_id, call.from_user.id)

    already_participant = bool(raffle_participant)
    await call.message.answer_photo(raffle[1], caption=raffle[3], parse_mode="HTML",
                                    reply_markup=get_raffle_kb(raffle_id, already_participant))


@router.callback_query(F.data.startswith("raffle_start:"))
async def func(call: CallbackQuery, state: FSMContext, bot):
    raffle_id = int(call.data.split(":")[1])
    raffle_participant = get_raffle_participant(raffle_id, call.from_user.id)
    if raffle_participant:
        return await call.answer("Вы уже участвуете в розыгрыше", show_alert=True)

    chat_member = await bot.get_chat_member(chat_id=config.CHANNEL_ID, user_id=call.from_user.id)
    if chat_member.status not in ["creator", "administrator", "member"]:
        return await call.answer("Для участия подпишитесь на наш канал @kgm_tg", show_alert=True)

    create_raffle_participant(raffle_id, call.from_user.id)
    await call.answer("Вы зарегистрировались в розыгрыше", show_alert=True)
