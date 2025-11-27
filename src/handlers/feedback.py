import sys
sys.path.append("../") # src/

from access import access_checker
from exceptions import exceptions_catcher
from states import makeNextStateCallback, makePrevStateCallback
from utils.common import respondEvent, getCallParams, getCurrentDateTime
from utils.feedback import makeFeedbackRequestMessage

from database.tables.feedback_requests import (
    getFeedbackRequest, 
    setFeedbackRequestTaken, 
    setFeedbackRequestCompleted,
    getLastUserFeedbackRequest
)
from database.tables.employees import getEmployee
from database.tables.users import getUser

from handlers.forms.add_feedback_request_form import start_add_feedback_request_form

from aiogram import Router, F, Bot
from aiogram.types import  CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext

from datetime import datetime


router = Router(name=__name__)


@router.callback_query(F.data.endswith("feedback/"))
@exceptions_catcher()
@access_checker()
async def feedback(event: CallbackQuery, state: FSMContext) -> None:
    await state.clear()

    message_text = (f"*📞 Обратная связь*")

    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text="📲 Отправить запрос", 
        callback_data=makeNextStateCallback(event, "add_feedback_request")
    )
    if prev_state := makePrevStateCallback(event):
        keyboard.button(text="⬅️ Назад", callback_data=prev_state)
    keyboard.adjust(1)

    await respondEvent(
        event,
        text=message_text, 
        parse_mode="Markdown",
        reply_markup=keyboard.as_markup()
    )


@router.callback_query(F.data.endswith("add_feedback_request/"))
@exceptions_catcher()
@access_checker()
async def add_feedback_request(event: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    await state.clear()

    telegram_id: int = event.from_user.id
    user_id: int = getUser(telegram_id=telegram_id)["id"]

    feedback_request: dict = getLastUserFeedbackRequest(user_id)
    if feedback_request:
        now: datetime = getCurrentDateTime().replace(tzinfo=None)
        created_at: datetime = feedback_request["created_at"]
        if (now - created_at).seconds < 60**2:
            return await bot.send_message(
                chat_id=telegram_id,
                text="*⏰ Вы можете оставить не более одной заявки на обратную связь в час*", 
                parse_mode="Markdown"
            )

    await start_add_feedback_request_form(event, state)


@router.callback_query(F.data.split("?")[0].endswith("take_feedback_request/"))
@exceptions_catcher()
@access_checker(required_permissions=["process_feedback_request"])
async def take_feedback_request(event: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    await state.clear()

    call_params: dict = getCallParams(event)
    feedback_request_id: int = call_params["feedback_request_id"]

    feedback_request: dict | None = getFeedbackRequest(feedback_request_id)
    if not feedback_request:
        return await respondEvent(event, text="*❌ Запрос на обратную связь не найден*", parse_mode="Markdown")

    employee_telegram_id: int = event.from_user.id
    employee_user_id: int = getUser(telegram_id=employee_telegram_id)["id"]
    employee_id: int = getEmployee(user_id=employee_user_id)["id"]

    current_employee_id: int = feedback_request["employee_id"]
    if current_employee_id and current_employee_id != employee_id:
        employee: dict = getEmployee(employee_id=current_employee_id)
        employee_fullname: str = employee["fullname"]
        return await respondEvent(
            event, 
            text=f"* ❌ Данный запрос на обратную связь уже принял в работу: {employee_fullname}*", 
            parse_mode="Markdown"
        )

    setFeedbackRequestTaken(
        feedback_request_id=feedback_request_id, 
        employee_id=employee_id
    )

    feedback_request: dict | None = getFeedbackRequest(feedback_request_id)
    feedback_request_message: str = makeFeedbackRequestMessage(feedback_request)

    # Employee message
    employee_message_text = (
        "*📥 Вы приняли запрос в работу*" + "\n\n"
        + feedback_request_message
    )
    employee_message_keyboard = InlineKeyboardBuilder()
    employee_message_keyboard.button(
        text="☑️ Отметить выполненным", 
        callback_data=f"complete_feedback_request/?feedback_request_id={feedback_request_id}"
    )
    await respondEvent(
        event, 
        text=employee_message_text,
        parse_mode="Markdown",
        reply_markup=employee_message_keyboard.as_markup()
    )

    # User message
    user_telegram_id: int = getUser(user_id=feedback_request["user_id"])["telegram_id"]
    user_message_text = (
        f"*⏳ Ваш запрос на обратную связь принят в работу*" + "\n\n"
        + feedback_request_message
    )
    await bot.send_message(chat_id=user_telegram_id, text=user_message_text, parse_mode="Markdown")


@router.callback_query(F.data.split("?")[0].endswith("complete_feedback_request/"))
@exceptions_catcher()
@access_checker(required_permissions=["process_feedback_request"])
async def complete_feedback_request(event: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    await state.clear()

    call_params: dict = getCallParams(event)
    feedback_request_id: int = call_params["feedback_request_id"]

    feedback_request: dict | None = getFeedbackRequest(feedback_request_id)
    if not feedback_request:
        return await respondEvent(event, text="*❌ Запрос на обратную связь не найден*", parse_mode="Markdown")

    setFeedbackRequestCompleted(feedback_request_id=feedback_request_id)

    feedback_request_message: str = makeFeedbackRequestMessage(feedback_request)

    # Employee message
    employee_telegram_id: int = event.from_user.id
    employee_message_text = (
        "*☑️ Вы отметили запрос на обратную связь как выполненный*" + "\n\n"
        + feedback_request_message
    )
    await respondEvent(event, text=employee_message_text, parse_mode="Markdown")

    # User message
    user_telegram_id: int = getUser(user_id=feedback_request["user_id"])["telegram_id"]
    user_message_text = (
        f"*☑️ Ваш запрос на обратную связь отмечен сотрудником как выполненный*" + "\n\n"
        + feedback_request_message
    )
    await bot.send_message(chat_id=user_telegram_id, text=user_message_text, parse_mode="Markdown")
