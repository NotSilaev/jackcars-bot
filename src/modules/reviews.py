import sys
sys.path.append("../") # src/

from config import settings
from api.telegram import TelegramAPI

from cache import setCacheValue, getCacheValue, DAY_SECONDS
from utils.reviews import makeReviewMessage

from database.tables.reviews import getReview
from database.tables.employees import getEmployee, getCarServiceEmployees
from database.tables.roles import getRole
from database.tables.users import getUser

import json


def alertReviewAdded(review_id: int) -> None:
    "Sends alerts to management about adding a new review."
        
    review: dict | None = getReview(review_id)
    if not review:
        return

    car_service_id: int = review["car_service_id"]

    management_roles = {
        "ceo": getRole(role_slug="ceo")["id"],
        "cto": getRole(role_slug="cto")["id"],
    }

    alert_recepients = []
    for role_slug, role_id in management_roles.items():
        management: str | None = getCacheValue(key=f"employees?role_slug={role_slug}")
        if management:
            management: list = json.loads(management)
        else:
            management: list = getCarServiceEmployees(car_service_id=car_service_id, role_id=role_id)
            setCacheValue(key=f"employees?role_slug={role_slug}", value=json.dumps(management), expire=DAY_SECONDS)
        alert_recepients.extend([employee["telegram_id"] for employee in management])

    if not alert_recepients:
        return

    review_message: str = makeReviewMessage(review)

    message_text = (
        "*🌟 Получен новый отзыв*" + "\n\n"
        + review_message
    )

    telegram_api = TelegramAPI(settings.TELEGRAM_BOT_TOKEN)
    for recepient in alert_recepients:
        telegram_api.sendRequest(
            request_method="POST",
            api_method="sendMessage",
            parameters={
                "chat_id": recepient,
                "text": message_text,
                "parse_mode": "Markdown",
            },
        )
