import sys
sys.path.append("../") # src/

from add_links import add_link_checker
from access import access_checker, hasEmployeeAccess
from exceptions import exceptions_catcher
from states import makeNextStateCallback
from utils.common import respondEvent, getUserName, makeGreetingMessage

from database.tables.users import getUser
from database.tables.employees import getEmployee

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext


router = Router(name=__name__)


@router.message(CommandStart())
@router.callback_query(F.data.endswith("start/"))
@router.message(F.text & (~F.text.startswith("/")), StateFilter(None))
@exceptions_catcher()
@add_link_checker()
@access_checker()
async def start(event: Message | CallbackQuery, state: FSMContext) -> None:
    await state.clear()

    telegram_user: User = event.from_user
    telegram_id: int = telegram_user.id
    user_name: str = getUserName(user=telegram_user)

    user: dict = getUser(telegram_id=telegram_id)
    user_id: int = user["id"]
    employee: dict | None = getEmployee(user_id=user_id)

    greeting: str = makeGreetingMessage()

    message_text = (
        f"*{greeting}*, {user_name}" + "\n\n"
        + "🧑🏼‍🔧 Чем я могу Вам помочь?"
    )

    keyboard = InlineKeyboardBuilder()

    if employee:
        if hasEmployeeAccess(employee, required_permissions=["add_user"]):
            keyboard.button(
                text="➕ Добавить пользователя", 
                callback_data=makeNextStateCallback(event, "add_user", is_start=True)
            )

    await respondEvent(
        event,
        text=message_text, 
        parse_mode="Markdown",
        reply_markup=keyboard.as_markup()
    )
