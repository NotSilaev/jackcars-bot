from aiogram.types import Message, CallbackQuery
from aiogram.types.user import User

from datetime import datetime
from zoneinfo import ZoneInfo
from decimal import Decimal
import qrcode
import uuid
import os


async def respondEvent(event: Message | CallbackQuery, **kwargs) -> int:
    "Responds to various types of events: messages and callback queries."

    if isinstance(event, Message):
        bot_message = await event.answer(**kwargs)
    elif isinstance(event, CallbackQuery):
        bot_message = await event.message.edit_text(**kwargs)
        await event.answer()

    return bot_message.message_id


def getCurrentDateTime(timezone_code: str = "Europe/Volgograd") -> datetime:
    timezone = ZoneInfo(timezone_code)
    current_datetime = datetime.now(tz=timezone)
    return current_datetime


def makeGreetingMessage(timezone_code: str = "Europe/Volgograd") -> str:
    "Generates a welcome message based on the current time of day."

    hour = getCurrentDateTime(timezone_code).hour

    if hour in range(0, 4) or hour in range(22, 24): # 22:00 - 4:00 is night
        greeting = "🌙 Доброй ночи"
    elif hour in range(4, 12): # 4:00 - 12:00 is morning
        greeting = "☕️ Доброе утро"
    elif hour in range(12, 18): # 12:00 - 18:00 is afternoon
        greeting = "☀️ Добрый день"
    elif hour in range(18, 22): # 18:00 - 22:00 is evening
        greeting = "🌆 Добрый вечер"
    else:
        greeting = "👋 Здравствуйте"
    
    return greeting


def getUserName(user: User) -> str:
    "Generates a string to address the user."

    user_id: int = user.id
    username: str = user.username
    first_name: str = user.first_name
    last_name: str = user.last_name
    
    if first_name:
        if last_name:
            user_name = f"{first_name} {last_name}"
        else:
            user_name = first_name
    elif username:
        user_name = f"@{username}"
    else:
        user_name = f"Пользователь №{user_id}"

    return user_name


def getCallParams(call: CallbackQuery) -> dict:
    "Parses the parameters from callback_data and returns them as a dictionary."

    try:
        call_params_list: list = call.data.split("?")[1].split("&")
    except IndexError:
        return {}

    call_params = {}
    for param in call_params_list:
        key, value = param.split("=")
        call_params[key] = value

    return call_params


def generateQRCode(qr_data: str, qr_img_name: str = None) -> str:
    dir_path = "media/temporary/qr"
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    qr_img = qrcode.make(qr_data)
    if not qr_img_name:
        qr_img_name = str(uuid.uuid4())
    qr_img_path = f'{dir_path}/{qr_img_name}.png'
    qr_img.save(qr_img_path)

    return qr_img_path


def removeFile(file_path: str) -> bool:
    "Deletes a local file from the machine."

    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False
