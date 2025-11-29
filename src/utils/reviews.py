from database.tables.users import getUser
from database.tables.car_services import getCarService


def makeReviewMessage(review: dict) -> str:
    "Generates a message with data about the review."

    user_id: int = review["user_id"]
    car_service_id: int = review["car_service_id"]
    text: str = review["text"]
    rating: str = review["rating"]

    user_phone: str = getUser(user_id=user_id)["phone"]
    car_service: str = getCarService(car_service_id=car_service_id)["name"]

    if not text:
        text = "не указан"

    review_message = (
        f"📞 Номер телефона: `{user_phone}`" + "\n\n"
        + f"🏎 Автосервис «JackCars»: *{car_service}*" + "\n"
        + f"💭 Текст: *{text}*" + "\n"
        + f"💫 Оценка: *{rating} ({'⭐️' * rating})*"
    )

    return review_message
