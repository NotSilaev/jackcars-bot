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
