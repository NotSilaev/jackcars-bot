import sys
sys.path.append("../../") # src/

from utils.common import getCurrentDateTime

from database import execute, fetch
from database.utils import makeQueryConditions

from datetime import datetime


def createEmployee(user_id: int, role_id: int, fullname: str) -> None:
    created_at: datetime = getCurrentDateTime()

    stmt = """
        INSERT INTO employees
        (user_id, role_id, fullname, created_at)
        VALUES (%s, %s, %s, %s)
    """
    
    params = (user_id, role_id, fullname, created_at)

    execute(stmt, params)


def getEmployee(employee_id: int = None, user_id: int = None) -> dict | None:
    if (not employee_id) and (not user_id):
        raise AttributeError("At least one argument must be passed")

    conditions_data: tuple = makeQueryConditions(id=employee_id, user_id=user_id)
    conditions_string, conditions_params = conditions_data

    query = f"""
        SELECT id, user_id, role_id, fullname, created_at
        FROM employees
        {conditions_string}
    """

    response: list = fetch(query, conditions_params, fetch_type="one", as_dict=True)

    try:
        employee: dict = response[0]
    except IndexError:
        employee = None

    return employee


def getCarServiceEmployees(car_service_id: int, role_id: int = None) -> list:
    if not role_id:
        query = "SELECT employee_id FROM car_services_employees WHERE car_service_id = %s"
        params = (car_service_id, )
    else:
        query = """
            SELECT cse.employee_id, e.user_id, u.telegram_id, e.role_id, e.fullname
            FROM car_services_employees cse
            JOIN employees e
                ON cse.employee_id = e.id
            JOIN users u
                ON u.id = e.user_id
            WHERE 
                car_service_id = %s
                AND e.role_id = %s
        """
        params = (car_service_id, role_id, )

    car_service_employees: list = fetch(query, params, fetch_type="all", as_dict=True)

    return car_service_employees
