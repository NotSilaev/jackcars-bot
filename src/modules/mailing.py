import sys
sys.path.append("../") # src/

from config import settings
from api.telegram import TelegramAPI
from utils.common import removeFile

from database.tables.users import getUsers

from aiogram.types import FSInputFile

import os


def sendMailing(mailing: dict) -> None:
    users: list = getUsers()

    message_text: str = mailing["text"]
    image_path: str = mailing["image_path"]
    
    telegram_api = TelegramAPI(settings.TELEGRAM_BOT_TOKEN)

    if image_path and os.path.exists(image_path):
        for user in users:
            telegram_id: int = user["telegram_id"]
            telegram_api.sendRequest(
                request_method="POST",
                api_method="sendPhoto",
                parameters={
                    "chat_id": telegram_id,
                    "caption": message_text,
                    "parse_mode": "Markdown",
                },
                files={
                    "photo": FSInputFile(image_path)
                }
            )
    else:
        for user in users:
            telegram_id: int = user["telegram_id"]
            telegram_api.sendRequest(
                request_method="POST",
                api_method="sendMessage",
                parameters={
                    "chat_id": telegram_id,
                    "text": message_text,
                    "parse_mode": "Markdown",
                },
            )

    removeFile(file_path=image_path)
