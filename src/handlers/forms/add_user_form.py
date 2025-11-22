import sys
sys.path.append("../../") # src/

from config import settings

from access import access_checker
from exceptions import exceptions_catcher
from utils.common import respondEvent, generateQRCode, removeFile

from database.tables.users import getUser
from database.tables.employees import getEmployee
from database.tables.add_links import createAddLink

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

import uuid
import re


router = Router(name=__name__)


class User(StatesGroup):
    phone = State()


async def start_add_user_form(event: CallbackQuery, state: FSMContext) -> None:
    await user_phone_state(event, state)


@router.callback_query(F.data == "user_phone_state")
@exceptions_catcher()
@access_checker(required_permissions=["add_user"])
async def user_phone_state(event: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(User.phone)

    message_text = (
        "*➕ Добавление пользователя*" + "\n\n"
        + "📲 Укажите номер телефона"
    )

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="❌ Отмена", callback_data="start/")

    await respondEvent(
        event,
        text=message_text,
        parse_mode="Markdown",
        reply_markup=keyboard.as_markup()
    )


@router.message(User.phone)
@exceptions_catcher()
@access_checker(required_permissions=["add_user"])
async def user_phone_process(event: Message, state: FSMContext) -> None:
    phone_pattern = r"^(\+?\d{1,4}[\s\-]?)?(\(?\d{1,4}\)?[\s\-]?)?[\d\s\-]{5,15}$"
    phone: str = event.text

    if not re.match(phone_pattern, phone):
        await respondEvent(
            event,
            text="*❗ Номер телефона указан некорректно, повторите попытку*",
            parse_mode="Markdown",
        )
        return await user_phone_state(event, state)

    await state.update_data(phone=phone)
    await commit_add_user_form(event, state)


@exceptions_catcher()
@access_checker(required_permissions=["add_user"])
async def commit_add_user_form(event: CallbackQuery, state: FSMContext) -> None:
    telegram_id: int = event.from_user.id
    user: dict = getUser(telegram_id=telegram_id)
    user_id: int = user["id"]
    employee: dict = getEmployee(user_id=user_id)
    employee_id: int = employee["id"]

    user_data = await state.get_data()
    user_phone: str = user_data["phone"]

    add_link_id = str(uuid.uuid4())
    data = {"phone": user_phone}
    createAddLink(
        add_link_id=add_link_id,
        employee_id=employee_id,
        data=data,
    )

    bot_username: str = settings.TELEGRAM_BOT_USERNAME
    add_link = f"https://t.me/{bot_username}?start={add_link_id}"

    qr_img_path = generateQRCode(qr_data=add_link, qr_img_name=add_link_id)
    message_text = (
        "*✅ Пригласительный QR-код создан*" + "\n\n"
        + f"📲 Номер телефона: `{user_phone}`" + "\n\n"
        + f"🔗 Ссылка для приглашения: `{add_link}` (нажмите для копирования)" + "\n\n"
        + "🤳🏼 QR и ссылка действительны до момента активации."
    )

    photo = FSInputFile(qr_img_path)
    await event.answer_photo(
        photo=photo, 
        caption=message_text, 
        parse_mode="Markdown"
    )
    await state.clear()

    removeFile(file_path=qr_img_path)
