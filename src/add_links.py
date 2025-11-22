from config import settings

from states import makeNextStateCallback

from database.tables.add_links import getAddLink, increaseAddLinkActivations
from database.tables.users import createUser, getUser

from api.telegram import TelegramAPI

from aiogram.types import Message, CallbackQuery

import functools
import json
import os


def add_link_checker(): 
    """
    Сhecks for the presence of an add_link in the start message 
    and creates a user if it is available and valid.
    """

    def container(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                event: Message | CallbackQuery = args[0]
                telegram_id = event.from_user.id
            except (IndexError, AttributeError):
                return await func(*args, **kwargs)

            if isinstance(event, CallbackQuery):
                return await func(*args, **kwargs)

            add_link_id = _extractAddLinkID(event)
            if not add_link_id:
                return await func(*args, **kwargs)

            if not _canActivateAddLink(add_link_id, telegram_id):
                return await func(*args, **kwargs)

            _activateAddLink(add_link_id, telegram_id)

            _sendSuccessfulActivationMessage(event, telegram_id)
            
        return wrapper
    return container


def _extractAddLinkID(event: Message) -> str | None:
    try:
        return event.text.split()[1]
    except (IndexError, AttributeError):
        return None


def _canActivateAddLink(add_link_id: str, telegram_id: int) -> bool:
    add_link = getAddLink(add_link_id)
    if not add_link:
        return False
    
    activations = add_link['activations']
    activations_limit = add_link['activations_limit']
    
    if activations >= activations_limit:
        return False

    user: dict | None = getUser(telegram_id=telegram_id)
    if user:
        return False

    return True


def _activateAddLink(add_link_id: str, telegram_id: int) -> None:
    add_link = getAddLink(add_link_id)
    phone = add_link['data']["phone"]
    createUser(telegram_id=telegram_id, phone=phone)
    increaseAddLinkActivations(add_link_id)


def _sendSuccessfulActivationMessage(event: Message, telegram_id: int) -> None:
    message_text = (
        "*👋 Рад Вас видеть!*\n\n"
        + "🚀 Ассистент «JackCars» активирован."
    )

    keyboard: str = json.dumps({
        "inline_keyboard": [[{
            "text": "🏠 Открыть меню",
            "callback_data": makeNextStateCallback(event, "start")
        }]]
    })

    telegram_api = TelegramAPI(settings.TELEGRAM_BOT_TOKEN)
    telegram_api.sendRequest(
        request_method="POST",
        api_method="sendMessage",
        parameters={
            "chat_id": telegram_id,
            "text": message_text,
            "parse_mode": "Markdown",
            "reply_markup": keyboard,
        },
    )
