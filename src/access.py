from config import settings

from database.tables.users import getUser
from database.tables.employees import getEmployee
from database.tables.permissions import getRolePermissions

from api.telegram import TelegramAPI

from aiogram.types import Message, CallbackQuery

import functools


def hasEmployeeAccess(employee: dict, required_permissions: tuple) -> bool:
    "Checks whether the employee has access permissions."

    employee_role_id: int = employee["role_id"]
    employee_permissions = [
        permission["slug"] for permission in getRolePermissions(employee_role_id)
    ]
    for permission in required_permissions:
        if permission not in employee_permissions:
            return False
    
    return True


def access_checker(required_permissions: tuple[str] = None): 
    "Checks the user's access permissions to the function."

    def container(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            is_execution_allowed = True

            event: Message | CallbackQuery = args[0]
            telegram_id = event.from_user.id

            user: dict | None = getUser(telegram_id=telegram_id)

            if "state" in kwargs.keys():
                state = kwargs["state"]
            else:
                state = None

            # Check user existance
            if not user:
                is_execution_allowed = False
                info_message_text = (
                    "*🧑🏼‍🔧 Бот предназначен для клиентов автосервиса «JackCars»*\n\n"
                    + "Вы можете обратиться к свободному сервисному консультанту \
                       в любом из наших сервисов для подключения к системе."
                )

            # Check user permissions
            if required_permissions:
                user_id: int = user["id"]
                employee: dict | None = getEmployee(user_id=user_id)
                if (not employee) or (not hasEmployeeAccess(employee, required_permissions)):
                    is_execution_allowed = False
                    info_message_text = "*🚫 У Вас недостаточно прав для доступа к данному разделу*"

            if is_execution_allowed is False:
                telegram_api = TelegramAPI(settings.TELEGRAM_BOT_TOKEN)
                telegram_api.sendRequest(
                    request_method="POST",
                    api_method="sendMessage",
                    parameters={
                        "chat_id": telegram_id,
                        "text": info_message_text,
                        "parse_mode": "Markdown",
                    },
                )
                if state: await state.clear()
                return
                
            await func(*args, **kwargs)

        return wrapper
    return container
