import sys
sys.path.append("../../") # src/

from config import settings

from access import access_checker
from exceptions import exceptions_catcher
from states import makeNextStateCallback, makePrevStateCallback, updateEventState
from utils.common import respondEvent, getCallParams, getCurrentDateTime, isDateInRange
from utils.forms import makeFormStateMessage
from utils.keyboard import makeItemsKeyboard
from utils.views import shortenFullname
from cache import setCacheValue, getCacheValue, DAY_SECONDS

from database.tables.car_services import getCarServices
from database.tables.roles import getRole
from database.tables.employees import getCarServiceEmployees
from database.tables.contact_methods import getContactMethods
from database.tables.users import getUser
from database.tables.feedback_requests import createFeedbackRequest

from modules.feedback import alertFeedbackRequested

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

import re
import json
from datetime import datetime


router = Router(name=__name__)



class FeedbackRequest(StatesGroup):
    car_service = State()
    employee = State()
    contact_method = State()
    request_reason = State()

    titles = {
        "car_service": "🏎 Автосервис «JackCars»",
        "employee": "👨🏼‍💻 Сотрудник",
        "contact_method": "☎️ Способ связи",
        "request_reason": "💭 Причина обращения",
    }



async def start_add_feedback_request_form(event: CallbackQuery, state: FSMContext) -> None:
    await feedback_request_car_service_state(event, state)



@router.callback_query(F.data == "feedback_request_car_service_state")
@exceptions_catcher()
@access_checker()
async def feedback_request_car_service_state(event: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(FeedbackRequest.car_service)

    form_state_message: str = await makeFormStateMessage(FeedbackRequest, state)

    message_text = (
        "*📲 Запрос обратной связи*" + "\n\n"
        + ((form_state_message + "\n\n") if form_state_message else "")
        + "🏎 Выберите автосервис в который хотите обратиться"
    )

    car_services: str | None = getCacheValue(key="car_services")
    if car_services:
        car_services: list = json.loads(car_services)
    else:
        car_services: list = getCarServices()
        setCacheValue(key="car_services", value=json.dumps(car_services), expire=DAY_SECONDS)

    keyboard: InlineKeyboardBuilder = makeItemsKeyboard(
        items_buttons=[
            {
                "text": car_service["name"], 
                "callback_data": f"car_service?id={car_service['id']}&name={car_service['name']}"
            } 
            for car_service in car_services
        ], 
        nav_buttons=[{"text": "❌ Отмена", "callback_data": "feedback/"}],
        row_length=2
    )

    await respondEvent(
        event,
        text=message_text,
        parse_mode="Markdown",
        reply_markup=keyboard.as_markup()
    )


@router.callback_query(FeedbackRequest.car_service)
@exceptions_catcher()
@access_checker()
async def feedback_request_car_service_process(event: CallbackQuery, state: FSMContext) -> None:
    call_params: dict = getCallParams(event)
    car_service_id = int(call_params["id"])
    car_service_name = call_params["name"]

    await state.update_data(car_service={"value": car_service_id, "view": car_service_name})

    await feedback_request_employee_state(event, state)



@router.callback_query(F.data == "feedback_request_employee_state")
@exceptions_catcher()
@access_checker()
async def feedback_request_employee_state(event: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(FeedbackRequest.employee)

    form_state_message: str = await makeFormStateMessage(FeedbackRequest, state)

    message_text = (
        "*📲 Запрос обратной связи*" + "\n\n"
        + form_state_message + "\n\n"
        + "👨🏼‍💻 Выберите сотрудника к которому хотите обратиться или пропустите данный шаг"
    )

    state_data: dict = await state.get_data()
    car_service_id: int = state_data["car_service"]["value"]
    manager_role_id: int = getRole(role_slug="manager")["id"]

    employees: str | None = getCacheValue(key="employees?role_slug=manager")
    if employees:
        employees: list = json.loads(employees)
    else:
        employees: list = getCarServiceEmployees(car_service_id=car_service_id, role_id=manager_role_id)
        setCacheValue(key="employees?role_slug=manager", value=json.dumps(employees), expire=DAY_SECONDS)

    keyboard: InlineKeyboardBuilder = makeItemsKeyboard(
        items_buttons=[
            {
                "text": shortenFullname(employee["fullname"]), 
                "callback_data": (
                    f"employee?id={employee['employee_id']}&fullname={shortenFullname(employee['fullname'])}"
                )
            } 
            for employee in employees
        ], 
        nav_buttons=[
            {"text": "⬅️ Назад", "callback_data": "feedback_request_car_service_state"},
            {"text": "↪️ Пропуск", "callback_data": "skip"},
            {"text": "❌ Отмена", "callback_data": "feedback/"},
        ],
        row_length=2
    )

    await respondEvent(
        event,
        text=message_text,
        parse_mode="Markdown",
        reply_markup=keyboard.as_markup()
    )


@router.callback_query(FeedbackRequest.employee)
@exceptions_catcher()
@access_checker()
async def feedback_request_employee_process(event: CallbackQuery, state: FSMContext) -> None:
    if event.data == "skip":
        await state.update_data(employee={"value": None})
        return await feedback_request_contact_method_state(event, state)

    call_params: dict = getCallParams(event)
    employee_id = int(call_params["id"])
    employee_fullname = call_params["fullname"]

    await state.update_data(employee={"value": employee_id, "view": employee_fullname})
    await feedback_request_contact_method_state(event, state)



@router.callback_query(F.data == "feedback_request_contact_method_state")
@exceptions_catcher()
@access_checker()
async def feedback_request_contact_method_state(event: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(FeedbackRequest.contact_method)

    form_state_message: str = await makeFormStateMessage(FeedbackRequest, state)

    message_text = (
        "*📲 Запрос обратной связи*" + "\n\n"
        + form_state_message + "\n\n"
        + "☎️ Выберите предпочтительный способ обратной связи или пропустите данный шаг"
    )

    contact_methods: str | None = getCacheValue(key="contact_methods")
    if contact_methods:
        contact_methods: list = json.loads(contact_methods)
    else:
        contact_methods: list = getContactMethods()
        setCacheValue(key="contact_methods", value=json.dumps(contact_methods), expire=DAY_SECONDS)

    keyboard: InlineKeyboardBuilder = makeItemsKeyboard(
        items_buttons=[
            {
                "text": contact_method["name"], 
                "callback_data": f"contact_method?id={contact_method['id']}&name={contact_method['name']}"
            } 
            for contact_method in contact_methods
        ], 
        nav_buttons=[
            {"text": "⬅️ Назад", "callback_data": "feedback_request_employee_state"},
            {"text": "↪️ Пропуск", "callback_data": "skip"},
            {"text": "❌ Отмена", "callback_data": "feedback/"},
        ],
        row_length=2
    )

    await respondEvent(
        event,
        text=message_text,
        parse_mode="Markdown",
        reply_markup=keyboard.as_markup()
    )


@router.callback_query(FeedbackRequest.contact_method)
@exceptions_catcher()
@access_checker()
async def feedback_request_contact_method_process(event: CallbackQuery, state: FSMContext) -> None:
    if event.data == "skip":
        await state.update_data(contact_method={"value": None})
        return await feedback_request_reason_state(event, state)

    call_params: dict = getCallParams(event)
    contact_method_id = int(call_params["id"])
    contact_method_name = call_params["name"]

    await state.update_data(contact_method={"value": contact_method_id, "view": contact_method_name})
    await feedback_request_reason_state(event, state)



@router.callback_query(F.data == "feedback_request_reason_state")
@exceptions_catcher()
@access_checker()
async def feedback_request_reason_state(event: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(FeedbackRequest.request_reason)

    form_state_message: str = await makeFormStateMessage(FeedbackRequest, state)

    message_text = (
        "*📲 Запрос обратной связи*" + "\n\n"
        + form_state_message + "\n\n"
        + "✏️ Кратко изложите причину обращения или пропустите данный шаг"
    )

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="⬅️ Назад", callback_data="feedback_request_contact_method_state")
    keyboard.button(text="↪️ Пропуск", callback_data="skip")
    keyboard.button(text="❌ Отмена", callback_data="feedback/")
    keyboard.adjust(3)

    await respondEvent(
        event,
        text=message_text,
        parse_mode="Markdown",
        reply_markup=keyboard.as_markup()
    )


@router.callback_query(FeedbackRequest.request_reason)
@router.message(FeedbackRequest.request_reason)
@exceptions_catcher()
@access_checker()
async def feedback_request_reason_process(event: Message | CallbackQuery, state: FSMContext) -> None:
    if isinstance(event, CallbackQuery) and event.data == "skip":
        await state.update_data(request_reason={"value": None})
        return await commit_add_feedback_request_form(event, state)

    request_reason_text: str = event.text
    if len(request_reason_text) > 200:
        await respondEvent(
            event,
            text="*❗Описание причины обращения не должно превышать 200 символов*",
            parse_mode="Markdown",
        )
        return await feedback_request_reason_state(event, state)

    await state.update_data(request_reason={"value": request_reason_text, "view": request_reason_text})
    await commit_add_feedback_request_form(event, state)



@router.callback_query(F.data == "commit_add_feedback_request_form")
@exceptions_catcher()
@access_checker()
async def commit_add_feedback_request_form(event: Message | CallbackQuery, state: FSMContext) -> None:
    await state.set_state(None)

    form_state_message: str = await makeFormStateMessage(FeedbackRequest, state)

    keyboard = InlineKeyboardBuilder()

    if isinstance(event, CallbackQuery) and event.data == "commit_add_feedback_request_form":
        telegram_id: int = event.from_user.id
        user_id: int = getUser(telegram_id=telegram_id)["id"]
        feedback_request_data: dict = await state.get_data()
        
        feedback_request_id: int = createFeedbackRequest(
            user_id=user_id,
            car_service_id=feedback_request_data["car_service"]["value"],
            employee_id=feedback_request_data["employee"]["value"],
            contact_method_id=feedback_request_data["contact_method"]["value"],
            request_reason=feedback_request_data["request_reason"]["value"],
        )

        alertFeedbackRequested(feedback_request_id)
        
        message_heading = "*✅ Запрос обратной связи отправлен*"
        keyboard.button(text="📞 Вернуться в меню", callback_data="feedback/")
    else:
        message_heading = "*📲 Запрос обратной связи*"
        keyboard.button(text="✉️ Отправить запрос", callback_data="commit_add_feedback_request_form")
        keyboard.button(text="⬅️ Назад", callback_data="feedback_request_reason_state")
        keyboard.button(text="❌ Отмена", callback_data="feedback/")
        keyboard.adjust(1, 2)

    now: datetime = getCurrentDateTime()
    date = now.date()
    year = date.year; month = date.month; day = date.day
    period = [datetime(year, month, day, 8, 0), datetime(year, month, day, 20, 0)]
    if isDateInRange(now, period):
        waiting_time_message = "📩 Наш менеджер свяжется с Вами в течение 15 минут"
    else:
        waiting_time_message = "📩 Наш менеджер свяжется с Вами в начале рабочего дня (работаем с 8:00 до 20:00)"

    message_text = (
        message_heading + "\n\n"
        + form_state_message + "\n\n"
        + waiting_time_message
    )

    await respondEvent(
        event,
        text=message_text,
        parse_mode="Markdown",
        reply_markup=keyboard.as_markup()
    )
