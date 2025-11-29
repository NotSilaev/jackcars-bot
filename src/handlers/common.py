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
    user: dict = getUser(telegram_id=telegram_id)
    user_id: int = user["id"]
    employee: dict | None = getEmployee(user_id=user_id)

    greeting: str = makeGreetingMessage()
    user_name: str = getUserName(user=telegram_user)

    message_text = (
        f"*{greeting}*, {user_name}" + "\n\n"
        + "🧑🏼‍🔧 Чем я могу Вам помочь?"
    )

    keyboard = InlineKeyboardBuilder()
    # Common buttons
    keyboard.button(text="📞 Обратная связь", callback_data=makeNextStateCallback(event, "feedback", is_start=True))
    keyboard.button(text="✏️ Оставить отзыв", callback_data=makeNextStateCallback(event, "add_review", is_start=True))
    
    # Employees buttons
    if employee:
        if hasEmployeeAccess(employee, required_permissions=["add_user"]):
            keyboard.button(
                text="➕ Добавить пользователя", 
                callback_data=makeNextStateCallback(event, "add_user", is_start=True)
            )                
        if hasEmployeeAccess(employee, required_permissions=["add_mailing"]):
            keyboard.button(
                text="✉️ Запустить рассылку", 
                callback_data=makeNextStateCallback(event, "add_mailing", is_start=True)
            )        
        if hasEmployeeAccess(employee, required_permissions=["process_feedback_request"]):
            keyboard.button(
                text="📬 Запросы обратной связи", 
                callback_data=makeNextStateCallback(
                    event, 
                    "feedback_requests_list", 
                    next_state_params={"list_view": "employee"},
                    is_start=True
                )
            )        
        if hasEmployeeAccess(employee, required_permissions=["get_stats"]):
            keyboard.button(
                text="📊 Статистика", 
                callback_data=makeNextStateCallback(event, "stats", is_start=True)
            )
    keyboard.adjust(1)

    await respondEvent(
        event,
        text=message_text, 
        parse_mode="Markdown",
        reply_markup=keyboard.as_markup()
    )
