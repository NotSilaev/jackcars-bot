import sys
sys.path.append("../") # src/

from config import settings
from api.telegram import TelegramAPI

from cache import setCacheValue, getCacheValue, DAY_SECONDS
from utils.feedback import makeFeedbackRequestMessage

from database.tables.feedback_requests import getFeedbackRequest
from database.tables.employees import getEmployee, getCarServiceEmployees
from database.tables.roles import getRole
from database.tables.users import getUser

import json


def alertFeedbackRequested(feedback_request_id: int) -> None:
    "Sends alerts to employees about adding a new feedback request."
        
    feedback_request: dict | None = getFeedbackRequest(feedback_request_id)
    if not feedback_request:
        return

    employee_id: int | None = feedback_request["employee_id"]
    car_service_id: int = feedback_request["car_service_id"]

    if employee_id:
        user_id: int = getEmployee(employee_id=employee_id)["user_id"]
        telegram_id: int = getUser(user_id=user_id)["telegram_id"]
        alert_recepients = [telegram_id]
    else:
        manager_role_id: int = getRole(role_slug="manager")["id"]
        employees: str | None = getCacheValue(key="employees?role_slug=manager")
        if employees:
            employees: list = json.loads(employees)
        else:
            employees: list = getCarServiceEmployees(car_service_id=car_service_id, role_id=manager_role_id)
            setCacheValue(key="employees?role_slug=manager", value=json.dumps(employees), expire=DAY_SECONDS)
        alert_recepients = [employee["telegram_id"] for employee in employees]

    if not alert_recepients:
        return

    feedback_request_message: str = makeFeedbackRequestMessage(feedback_request)

    message_text = (
        "*📩 Получен запрос на обратную связь*" + "\n\n"
        + feedback_request_message
        + (
            ("\n\n" 
                + f"‼️ Пользователь выбрал Вас ответственным за ответ на данный запрос, другие сотрудники его не видят."
            ) if employee_id else ""
        )

    )

    keyboard = json.dumps({
        "inline_keyboard": [[{
            "text": "📥 Принять запрос",
            "callback_data": f"take_feedback_request/?feedback_request_id={feedback_request_id}"
        }]]
    })

    telegram_api = TelegramAPI(settings.TELEGRAM_BOT_TOKEN)
    for recepient in alert_recepients:
        telegram_api.sendRequest(
            request_method="POST",
            api_method="sendMessage",
            parameters={
                "chat_id": recepient,
                "text": message_text,
                "parse_mode": "Markdown",
                "reply_markup": keyboard,
            },
        )
