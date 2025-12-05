import sys
sys.path.append("../") # src/

from utils.common import isDateInRange

from utils.common import getCallParams
from states import updateStateCallbackParams

from database.tables.add_links import getAddLinks
from database.tables.feedback_requests import getFeedbackRequests
from database.tables.car_services import getEmployeeCarServices, getCarService
from database.tables.employees import getEmployee

from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

import abc
from datetime import datetime


STATS_BLOCKS = {
    "users": {
        "name": "🧑🏼‍💼 Пользователи",
        "class": "UsersStats",
    },
    "feedback_requests": {
        "name": "📞 Запросы обратной связи", 
        "class": "FeedbackRequestsStats",
    },
}


class StatsBlock(abc.ABC):
    def __init__(self, event: CallbackQuery = None, period: tuple[datetime, datetime] = None) -> None:
        self.event = event
        self.period = period
        if period:
            start_datetime, end_datetime = period
            self.period_text = "\n\n" + f"📅 Период с *{start_datetime.date()}* по *{end_datetime.date()}*"
        else:
            self.period_text = ""

    @abc.abstractmethod
    def makeText(self) -> str: pass

    def makeKeyboard(self) -> InlineKeyboardBuilder: 
        keyboard = InlineKeyboardBuilder()

        if not self.event:
            return keyboard

        call_params: dict = getCallParams(self.event)
        try:
            current_period_id = call_params["period_id"]
        except KeyError:
            current_period_id = None

        periods = {
            "day": "День",
            "week": "Неделя",
            "month": "Месяц",
            "year": "Год",
        }

        row_items = []
        period_idx = -1
        for period_id, period_name in periods.items():
            period_idx += 1
            row_items.append(
                InlineKeyboardButton(
                    text=f"▫️ {period_name}" if period_id == current_period_id else period_name, 
                    callback_data=updateStateCallbackParams(
                        event_or_state_callback=self.event, 
                        new_state_params={"period_id": period_id}, 
                        save_unchanged=True
                    ) if period_id != current_period_id else "#"
                )
            )
            if period_idx == len(periods.items())-1 or len(row_items) == 2:
                keyboard.row(*row_items)
                row_items.clear()

        if current_period_id:
            keyboard.row(InlineKeyboardButton(
                text="🗑 Сбросить период",
                callback_data=updateStateCallbackParams(
                    event_or_state_callback=self.event, 
                    new_state_params={"period_id": None}, 
                    save_unchanged=True
                )
            ))

        return keyboard


def getStatsBlock(block_id: str) -> StatsBlock:
    class_name = STATS_BLOCKS[block_id]["class"]
    return globals()[class_name]


class UsersStats(StatsBlock):
    def makeText(self) -> str:
        add_links: list = getAddLinks()

        employees_add_links_activations = {}
        for add_link in add_links:
            employee_id: int = add_link["employee_id"]
            activations: int = add_link["activations"]
            created_at: datetime = add_link["created_at"]

            if (
                activations == 0
                or (self.period and isDateInRange(created_at, self.period) is False)
            ):
                continue

            if employee_id not in employees_add_links_activations.keys():
                employees_add_links_activations[employee_id] = 0
            employees_add_links_activations[employee_id] += activations


        car_services_add_links_activations = {}
        for employee_id, activations in employees_add_links_activations.items():
            employee: dict = getEmployee(employee_id=employee_id)
            employee_fullname: str = employee["fullname"]
            employee_car_services: list = getEmployeeCarServices(employee_id=employee_id)

            if not employee_car_services:
                continue

            car_service_id: int = employee_car_services[0]["car_service_id"]

            if car_service_id not in car_services_add_links_activations.keys():
                car_services_add_links_activations[car_service_id] = {
                    "common": 0,
                    "employees": []
                }

            car_services_add_links_activations[car_service_id]["common"] += activations
            car_services_add_links_activations[car_service_id]["employees"].append(
                {"fullname": employee_fullname, "activations": activations}
            )


        add_links_activations_text_items = []

        for car_service_id, car_service_data in car_services_add_links_activations.items():
            car_service: dict = getCarService(car_service_id=car_service_id)
            car_service_name: str = car_service["name"]

            common_activations: int = car_service_data["common"]
            employees_activations: list[dict] = car_service_data["employees"]

            car_service_text_items = []
            for employee in employees_activations:
                employee_fullname: str = employee["fullname"]
                employee_activations: int = employee["activations"]
                car_service_text_items.append(f"╭➤ {employee_fullname}: *{employee_activations}*")

            car_service_text = (
                f"• {car_service_name}: {common_activations}" + "\n"
                + "\n".join(car_service_text_items)
            )

            add_links_activations_text_items.append(car_service_text)

        add_links_activations_text = (
            f"*{'—'*3} ➕ Добавлено пользователей {'—'*3}*" + "\n"
            + (
                "\n\n".join(add_links_activations_text_items) if add_links_activations_text_items 
                else "🔎 Нет данных"
            )
        )

        text = (
            "*🧑🏼‍💼 Статистика | Пользователи*" + "\n\n"
            + add_links_activations_text
            + self.period_text
        )
        return text


class FeedbackRequestsStats(StatsBlock):
    def makeText(self) -> str:
        feedback_requests = getFeedbackRequests()

        car_services_completed_feedback_requests = {}
        for feedback_request in feedback_requests:
            car_service_id: int = feedback_request["car_service_id"]
            employee_id: int = feedback_request["employee_id"]
            completed_at: datetime = feedback_request["completed_at"]

            if (
                completed_at is None
                or (self.period and isDateInRange(completed_at, self.period) is False)
            ):
                continue

            if car_service_id not in car_services_completed_feedback_requests:
                car_services_completed_feedback_requests[car_service_id] = {
                    "common": 0,
                    "employees": {}
                }

            if employee_id not in car_services_completed_feedback_requests[car_service_id]["employees"]:
                employee: dict = getEmployee(employee_id=employee_id)
                employee_fullname: str = employee["fullname"]
                car_services_completed_feedback_requests[car_service_id]["employees"][employee_id] = {
                    "fullname": employee_fullname, 
                    "completed": 0
                }

            car_services_completed_feedback_requests[car_service_id]["common"] += 1
            car_services_completed_feedback_requests[car_service_id]["employees"][employee_id]["completed"] += 1


        completed_feedback_requests_text_items = []

        for car_service_id, car_service_data in car_services_completed_feedback_requests.items():
            car_service: dict = getCarService(car_service_id=car_service_id)
            car_service_name: str = car_service["name"]

            common_completed: int = car_service_data["common"]
            employees_completed: list[dict] = car_service_data["employees"]

            car_service_text_items = []
            for employee in employees_completed.values():
                employee_fullname: str = employee["fullname"]
                employee_completed: int = employee["completed"]
                car_service_text_items.append(f"╭➤ {employee_fullname}: *{employee_completed}*")

            car_service_text = (
                f"• {car_service_name}: {common_completed}" + "\n"
                + "\n".join(car_service_text_items)
            )

            completed_feedback_requests_text_items.append(car_service_text)

        completed_feedback_requests_text = (
            f"*{'—'*3} ✅ Обработано запросов {'—'*3}*" + "\n"
            + (
                "\n\n".join(completed_feedback_requests_text_items) if completed_feedback_requests_text_items 
                else "🔎 Нет данных"
            )
        )


        text = (
            "*📞 Статистика | Запросы обратной связи*" + "\n\n"
            + completed_feedback_requests_text
            + self.period_text
        )
        return text
