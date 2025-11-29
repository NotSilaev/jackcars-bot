import sys
sys.path.append("../") # src/

from access import access_checker, hasEmployeeAccess
from exceptions import exceptions_catcher
from states import makeNextStateCallback, makePrevStateCallback, reduceStateData
from utils.common import respondEvent, getCallParams, getCurrentDateTime
from utils.feedback import makeFeedbackRequestMessage
from utils.pagination import Paginator

from database.tables.feedback_requests import (
    getFeedbackRequest, 
    getFeedbackRequests, 
    setFeedbackRequestTaken, 
    setFeedbackRequestCompleted,
    getLastUserFeedbackRequest
)
from database.tables.employees import getEmployee
from database.tables.users import getUser
from database.tables.car_services import getEmployeeCarServices

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
    keyboard.button(
        text="🗃 Список моих запросов", 
        callback_data=makeNextStateCallback(event, "feedback_requests_list", next_state_params={"list_view": "user"})
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


@router.callback_query(
    F.data.split("?")[-2].endswith("feedback_requests_list/")
    | F.data.split("?")[-2].endswith(reduceStateData("feedback_requests_list") + "/")
)
@exceptions_catcher()
@access_checker()
async def feedback_requests_list(event: CallbackQuery, state: FSMContext) -> None:
    await state.clear()

    telegram_id: int = event.from_user.id
    user_id: int = getUser(telegram_id=telegram_id)["id"]

    call_params: dict = getCallParams(event)
    try:
        list_view: str = call_params["list_view"]
    except KeyError:
        list_view: str = "user"

    if list_view == "user":
        feedback_requests: list = getFeedbackRequests(user_id=user_id, completed_at_is_null=True)
    elif list_view == "employee":
        employee: dict | None = getEmployee(user_id=user_id)
        if employee and hasEmployeeAccess(employee, required_permissions=["process_feedback_request"]):
            employee_id: int = employee["id"]
            employee_car_services: int = getEmployeeCarServices(employee_id=employee_id)
            feedback_requests = []
            for car_service in employee_car_services:
                feedback_requests.extend(
                    getFeedbackRequests(car_service_id=car_service["car_service_id"], completed_at_is_null=True)
                )
            for feedback_request in feedback_requests:
                feedback_request_employee_id: int | None = feedback_request["employee_id"]
                if feedback_request_employee_id and feedback_request_employee_id != employee_id:
                    feedback_requests.remove(feedback_request)

    message_text = (
        "*🗃 Список запросов*" + "\n\n"
        + (
            f"⏳ Активных запросов: *{len(feedback_requests)}*" if feedback_requests 
            else "🔎 Нет ни одного активного запроса"
        )
    )

    if feedback_requests:
        feedback_requests_keyboard_items = []
        for feedback_request in feedback_requests:
            feedback_request_id: int = feedback_request["id"]

            phone: str = getUser(user_id=feedback_request["user_id"])["phone"]
            request_reason: str = feedback_request["request_reason"]
            created_at_date: datetime = feedback_request["created_at"].date()

            if list_view == "user":
                if request_reason:
                    feedback_request_button = f"{created_at_date} | {request_reason}"
                else:
                    feedback_request_button = f"{created_at_date}"
            elif list_view == "employee":
                if request_reason:
                    feedback_request_button = f"{phone} | {request_reason}"
                else:
                    feedback_request_button = f"{phone}"

            feedback_requests_keyboard_items.append({
                "text": feedback_request_button, 
                "callback_data": makeNextStateCallback(
                    event,
                    reduceStateData("feedback_request_card"),
                    next_state_params={reduceStateData("feedback_request_id"): feedback_request_id}
                )
            })

        try:
            page = int(call_params["page"])
        except KeyError:
            page = 1

        paginator = Paginator(
            array=feedback_requests_keyboard_items,
            offset=5,
            page_callback=makeNextStateCallback(event, reduceStateData("feedback_requests_list")),
            back_callback=makePrevStateCallback(event)
        )
        keyboard: InlineKeyboardBuilder = paginator.makePageKeyboard(page=page)
    elif not feedback_requests:
        keyboard = InlineKeyboardBuilder()
        if prev_state := makePrevStateCallback(event):
            keyboard.button(text="⬅️ Назад", callback_data=prev_state)

    await respondEvent(
        event,
        text=message_text, 
        parse_mode="Markdown",
        reply_markup=keyboard.as_markup()
    )


@router.callback_query(
    F.data.split("?")[-2].endswith("feedback_request_card/")
    | F.data.split("?")[-2].endswith(reduceStateData("feedback_request_card") + "/")
)
@exceptions_catcher()
@access_checker()
async def feedback_request_card(event: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    await state.clear()

    telegram_id: int = event.from_user.id

    call_params: dict = getCallParams(event)
    try:
        feedback_request_id = int(call_params["feedback_request_id"])
    except KeyError:
        feedback_request_id = int(call_params[reduceStateData("feedback_request_id")])

    feedback_request: dict | None = getFeedbackRequest(feedback_request_id)
    feedback_request_message: str = makeFeedbackRequestMessage(feedback_request)

    message_text = (
        "*📨 Запрос обратной связи*" + "\n\n"
        + feedback_request_message
    )

    keyboard = InlineKeyboardBuilder()

    user_id: int = getUser(telegram_id=telegram_id)["id"]
    employee: dict | None = getEmployee(user_id=user_id)
    if employee:
        if (feedback_request["employee_id"] is None) or (feedback_request["employee_id"] == employee["id"]):
            if not feedback_request["taken_at"]:
                keyboard.button(
                    text="📥 Принять запрос", 
                    callback_data=f"take_feedback_request/?feedback_request_id={feedback_request_id}"
                )
            elif not feedback_request["completed_at"]:
                keyboard.button(
                    text="☑️ Отметить выполненным", 
                    callback_data=f"complete_feedback_request/?feedback_request_id={feedback_request_id}"
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
    taken_at: datetime = feedback_request["taken_at"]
    if current_employee_id:
        message_text = None
        if current_employee_id != employee_id:
            employee: dict = getEmployee(employee_id=current_employee_id)
            employee_fullname: str = employee["fullname"]
            message_text = f"* ❌ Данный запрос на обратную связь уже принял в работу: {employee_fullname}*"
        elif taken_at and (current_employee_id == employee_id):
            message_text = f"* ❌ Вы уже приняли данный запрос в работу*"
        if message_text:
            return await respondEvent(
                event, 
                text=message_text, 
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

    completed_at: datetime = feedback_request["completed_at"]
    if completed_at:
        return await respondEvent(
            event, 
            text="*❌ Вы уже отметили данный запрос выполненным*", 
            parse_mode="Markdown"
        )

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
