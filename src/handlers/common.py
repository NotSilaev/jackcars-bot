import sys
sys.path.append("../") # src/

from exceptions import exceptions_catcher
from states import makeNextStateCallback
from utils.common import respondEvent, getUserName, makeGreetingMessage

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
async def start(event: Message | CallbackQuery, state: FSMContext) -> None:
    await state.clear()

    telegram_user: User = event.from_user
    telegram_id: int = telegram_user.id
    user_name: str = getUserName(user=telegram_user)

    greeting: str = makeGreetingMessage()

    message_text = (
        f"*{greeting}*, {user_name}"
    )

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Hello, World!", callback_data=makeNextStateCallback(event, "#", is_start=True))

    await respondEvent(
        event,
        text=message_text, 
        parse_mode="Markdown",
        reply_markup=keyboard.as_markup()
    )
