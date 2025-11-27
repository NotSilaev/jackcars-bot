from database.tables.users import getUser
from database.tables.car_services import getCarService
from database.tables.employees import getEmployee
from database.tables.contact_methods import getContactMethod


def makeFeedbackRequestMessage(feedback_request: dict) -> str:
    "Generates a message with data about the feedback request."

    car_service_id: int = feedback_request["car_service_id"]
    employee_id: int | None = feedback_request["employee_id"]
    user_id: int = feedback_request["user_id"]
    contact_method_id: int | None = feedback_request["contact_method_id"]
    request_reason: str | None = feedback_request["request_reason"]

    user_phone: str = getUser(user_id=user_id)["phone"]
    car_service: str = getCarService(car_service_id=car_service_id)["name"]

    if employee_id:
        employee: str = getEmployee(employee_id=employee_id)["fullname"]
    else:
        employee = "не назначен"

    if contact_method_id:
        contact_method: str = getContactMethod(contact_method_id=contact_method_id)["name"]
    else:
        contact_method = "не указан"

    if not request_reason:
        request_reason = "не указана"

    feedback_request_message = (
        f"📞 Номер телефона: `{user_phone}`" + "\n\n"
        + f"🏎 Автосервис «JackCars»: *{car_service}*" + "\n"
        + f"👨🏼‍💻 Сотрудник: *{employee}*" + "\n"
        + f"☎️ Способ связи: *{contact_method}*" + "\n"
        + f"💭 Причина обращения: *{request_reason}*"
    )

    return feedback_request_message
