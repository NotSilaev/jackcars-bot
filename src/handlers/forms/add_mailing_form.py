import sys
sys.path.append("../../") # src/

from config import settings

from access import access_checker
from exceptions import exceptions_catcher
from utils.common import respondEvent, getCallParams, getCurrentDateTime
from utils.forms import makeFormStateMessage
from utils.keyboard import makeItemsKeyboard
from cache import setCacheValue, getCacheValue, DAY_SECONDS

from modules.mailing import sendMailing

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types.photo_size import PhotoSize

import json
import uuid
import re


router = Router(name=__name__)



class Mailing(StatesGroup):
    text = State()
    image = State()

    titles = {
        "text": "💭 Текст",
        "image": "📷 Изображение",
    }



async def start_add_mailing_form(event: CallbackQuery, state: FSMContext) -> None:
    await mailing_text_state(event, state)



@router.callback_query(F.data == "mailing_text_state")
@exceptions_catcher()
@access_checker(required_permissions=["add_mailing"])
async def mailing_text_state(event: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Mailing.text)

    form_state_message: str = await makeFormStateMessage(Mailing, state)

    message_text = (
        "*✉️ Запуск рассылки*" + "\n\n"
        + ((form_state_message + "\n\n") if form_state_message else "")
        + "📝 Введите текст рассылки"
    )

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="❌ Отмена", callback_data="start/")

    await respondEvent(
        event,
        text=message_text,
        parse_mode="Markdown",
        reply_markup=keyboard.as_markup()
    )
    

@router.message(Mailing.text)
@exceptions_catcher()
@access_checker(required_permissions=["add_mailing"])
async def mailing_text_process(event: Message, state: FSMContext) -> None:
    text: str = event.text

    if len(text) < 20 or len(text) > 1000:
        await respondEvent(
            event,
            text="*‼️ Текст рассылки должен содержать от 20 до 1000 символов*",
            parse_mode="Markdown",
        )
        return await mailing_text_state(event, state)

    await state.update_data(text={"value": text, "view": text})
    await mailing_image_state(event, state)



@router.callback_query(F.data == "mailing_image_state")
@exceptions_catcher()
@access_checker(required_permissions=["add_mailing"])
async def mailing_image_state(event: Message, state: FSMContext) -> None:
    await state.set_state(Mailing.image)

    form_state_message: str = await makeFormStateMessage(Mailing, state)

    message_text = (
        "*✉️ Запуск рассылки*" + "\n\n"
        + form_state_message + "\n\n"
        + "📷 Добавьте изображение или пропустите данный шаг"
    )

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="⬅️ Назад", callback_data="mailing_text_state")
    keyboard.button(text="↪️ Пропустить", callback_data="skip")
    keyboard.button(text="❌ Отмена", callback_data="start/")
    keyboard.adjust(3)


    await respondEvent(
        event,
        text=message_text,
        parse_mode="Markdown",
        reply_markup=keyboard.as_markup()
    )


@router.message(Mailing.image)
@router.callback_query(Mailing.image)
@exceptions_catcher()
@access_checker(required_permissions=["add_mailing"])
async def mailing_image_process(event: Message | CallbackQuery, state: FSMContext, bot: Bot) -> None:
    if isinstance(event, CallbackQuery) and event.data == "skip":
        await state.update_data(image={"value": None})
        return await commit_add_mailing_form(event, state)

    if event.photo:
        image: PhotoSize = event.photo[-1]
    else:
        await respondEvent(
            event,
            text="*‼️ Отправьте изображение или пропустите текущий шаг*",
            parse_mode="Markdown",
        )
        return await mailing_image_state(event, state)

    image_id: str = image.file_id
    image_name = f"{image_id}.jpg"    
    image_path = f"media/temporary/mailing/{image_name}"
    await bot.download(file=image_id, destination=image_path)

    await state.update_data(image={"value": image_path, "view": "добавлено"})
    await commit_add_mailing_form(event, state)



@router.callback_query(F.data == "commit_add_mailing_form")
@exceptions_catcher()
@access_checker()
async def commit_add_mailing_form(event: Message | CallbackQuery, state: FSMContext) -> None:
    await state.set_state(None)

    form_state_message: str = await makeFormStateMessage(Mailing, state)

    keyboard = InlineKeyboardBuilder()

    if isinstance(event, CallbackQuery) and event.data == "commit_add_mailing_form":
        mailing_data: dict = await state.get_data()
        mailing = {
            "text": mailing_data["text"]["value"],
            "image_path": mailing_data["image"]["value"],
        }
        sendMailing(mailing)

        message_heading = "*📨 Процесс отправки сообщений запущен.*"
        await state.clear()
    else:
        message_heading = "*✉️ Запуск рассылки*"
        keyboard.button(text="📨 Запустить рассылку", callback_data="commit_add_mailing_form")
        keyboard.button(text="⬅️ Назад", callback_data="review_rating_state")
        keyboard.button(text="❌ Отмена", callback_data="start/")
        keyboard.adjust(1, 2)

    message_text = (
        message_heading + "\n\n"
        + form_state_message
    )

    await respondEvent(
        event,
        text=message_text,
        parse_mode="Markdown",
        reply_markup=keyboard.as_markup()
    )

