import sys
sys.path.append("../../") # src/

from config import settings

from access import access_checker
from exceptions import exceptions_catcher
from utils.common import respondEvent, getCallParams, getCurrentDateTime
from utils.forms import makeFormStateMessage
from utils.keyboard import makeItemsKeyboard
from cache import setCacheValue, getCacheValue, DAY_SECONDS

from database.tables.car_services import getCarServices, getCarService
from database.tables.users import getUser
from database.tables.reviews import getUserReviews, createReview

from modules.reviews import alertReviewAdded

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

import json
import uuid
import re


router = Router(name=__name__)



class Review(StatesGroup):
    car_service = State()
    text = State()
    rating = State()

    titles = {
        "car_service": "🏎 Автосервис «JackCars»",
        "text": "💭 Текст",
        "rating": "💫 Оценка",
    }



async def start_add_review_form(event: CallbackQuery, state: FSMContext) -> None:
    await review_car_service_state(event, state)



@router.callback_query(F.data == "review_car_service_state")
@exceptions_catcher()
@access_checker()
async def review_car_service_state(event: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Review.car_service)

    form_state_message: str = await makeFormStateMessage(Review, state)

    message_text = (
        "*✏️ Добавление отзыва*" + "\n\n"
        + ((form_state_message + "\n\n") if form_state_message else "")
        + "🏎 Выберите автосервис работу которого хотите оценить"
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
        nav_buttons=[{"text": "❌ Отмена", "callback_data": "start/"}],
        row_length=2
    )

    await respondEvent(
        event,
        text=message_text,
        parse_mode="Markdown",
        reply_markup=keyboard.as_markup()
    )


@router.callback_query(Review.car_service)
@exceptions_catcher()
@access_checker()
async def review_car_service_process(event: CallbackQuery, state: FSMContext) -> None:
    call_params: dict = getCallParams(event)
    car_service_id = int(call_params["id"])
    car_service_name = call_params["name"]

    telegram_id: int = event.from_user.id
    user_id: int = getUser(telegram_id=telegram_id)["id"]

    user_reviews: dict = getUserReviews(user_id=user_id)
    for review in user_reviews:
        if car_service_id == review["car_service_id"]:
            await state.clear()

            message_text = (
                "*🏆 Вы уже оценили данный автосервис!*" + "\n\n"
                + "🤩 Но Вы также всегда можете поставить нам оценку на *Яндекс.Картах*!"
            )

            car_service: dict = getCarService(car_service_id)
            car_service_yandex_maps_url: str = car_service["yandex_maps_url"]

            keyboard = InlineKeyboardBuilder()
            keyboard.button(
                text="🌟 Оценить на Яндекс.Картах", 
                url=car_service_yandex_maps_url,
            )

            return await respondEvent(
                event,
                text=message_text, 
                parse_mode="Markdown",
                reply_markup=keyboard.as_markup()
            )

    await state.update_data(car_service={"value": car_service_id, "view": car_service_name})
    await review_text_state(event, state)



@router.callback_query(F.data == "review_text_state")
@exceptions_catcher()
@access_checker()
async def review_text_state(event: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Review.text)

    form_state_message: str = await makeFormStateMessage(Review, state)

    message_text = (
        "*✏️ Добавление отзыва*" + "\n\n"
        + form_state_message + "\n\n"
        + "📝 Поделитесь своим мнением о качестве обслуживания в автосервисе «JackCars» или пропустите данный шаг."
    )

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="⬅️ Назад", callback_data="review_car_service_state")
    keyboard.button(text="↪️ Пропустить", callback_data="skip")
    keyboard.button(text="❌ Отмена", callback_data="start/")
    keyboard.adjust(3)

    await respondEvent(
        event,
        text=message_text,
        parse_mode="Markdown",
        reply_markup=keyboard.as_markup()
    )


@router.message(Review.text)
@router.callback_query(Review.text)
@exceptions_catcher()
@access_checker()
async def review_text_process(event: Message | CallbackQuery, state: FSMContext) -> None:
    if isinstance(event, CallbackQuery) and event.data == "skip":
        await state.update_data(text={"value": None})
        return await review_rating_state(event, state)

    text: str = event.text

    if len(text) < 20 or len(text) > 2000:
        await respondEvent(
            event,
            text="*‼️ Текст отзыва должен содержать от 20 до 2000 символов*",
            parse_mode="Markdown",
        )
        return await review_text_state(event, state)

    await state.update_data(text={"value": text, "view": text})
    await review_rating_state(event, state)



@router.callback_query(F.data == "review_rating_state")
@exceptions_catcher()
@access_checker()
async def review_rating_state(event: Message | CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Review.rating)

    form_state_message: str = await makeFormStateMessage(Review, state)

    message_text = (
        "*✏️ Добавление отзыва*" + "\n\n"
        + form_state_message + "\n\n"
        + "💫 Оцените качество обслуживания по пятибальной шкале."
    )

    keyboard = InlineKeyboardBuilder()
    for rating in range(1, 5+1):
        keyboard.button(text=("⭐️" * rating), callback_data=f"rating?value={rating}")
    keyboard.button(text="⬅️ Назад", callback_data="review_text_state")
    keyboard.button(text="❌ Отмена", callback_data="start/")
    keyboard.adjust(*(1 for _ in range(0, 5)), 2)

    await respondEvent(
        event,
        text=message_text,
        parse_mode="Markdown",
        reply_markup=keyboard.as_markup()
    )


@router.callback_query(Review.rating)
@exceptions_catcher()
@access_checker()
async def review_rating_process(event: CallbackQuery, state: FSMContext) -> None:
    call_params: dict = getCallParams(event)
    rating = int(call_params["value"])

    await state.update_data(rating={"value": rating, "view": f"{rating} ({'⭐️' * rating})"})
    await commit_add_review_form(event, state)



@router.callback_query(F.data == "commit_add_review_form")
@exceptions_catcher()
@access_checker()
async def commit_add_review_form(event: Message | CallbackQuery, state: FSMContext) -> None:
    await state.set_state(None)

    form_state_message: str = await makeFormStateMessage(Review, state)

    keyboard = InlineKeyboardBuilder()

    if isinstance(event, CallbackQuery) and event.data == "commit_add_review_form":
        telegram_id: int = event.from_user.id
        user_id: int = getUser(telegram_id=telegram_id)["id"]
        review_data: dict = await state.get_data()

        car_service_id: int = review_data["car_service"]["value"]
        car_service: dict = getCarService(car_service_id)
        car_service_yandex_maps_url: str = car_service["yandex_maps_url"]
        
        review_id: int = createReview(
            user_id=user_id,
            car_service_id=car_service_id,
            text=review_data["text"]["value"],
            rating=review_data["rating"]["value"]
        )
        alertReviewAdded(review_id)
        
        message_heading = "*🎉 Отзыв сохранён. Спасибо, каждая оценка очень важна для нас!*"
        yandex_review_message = (
            "*🤩 Мы также будем благодарны за оценку качества нашего обслуживания на Яндекс.Картах!*"
        )
        keyboard.button(
            text="🌟 Оценить на Яндекс.Картах", 
            url=car_service_yandex_maps_url,
        )
        keyboard.button(text="🏠 Вернуться в главное меню", callback_data="start/")
        keyboard.adjust(1)
    else:
        message_heading = "*✏️ Добавление отзыва*"
        yandex_review_message = ""
        keyboard.button(text="📤 Отправить отзыв", callback_data="commit_add_review_form")
        keyboard.button(text="⬅️ Назад", callback_data="review_rating_state")
        keyboard.button(text="❌ Отмена", callback_data="start/")
        keyboard.adjust(1, 2)

    message_text = (
        message_heading + "\n\n"
        + form_state_message + "\n\n"
        + yandex_review_message
    )

    await respondEvent(
        event,
        text=message_text,
        parse_mode="Markdown",
        reply_markup=keyboard.as_markup()
    )
