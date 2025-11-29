import sys
sys.path.append("../../") # src/

from utils.common import getCurrentDateTime

from database import execute, fetch
from database.utils import makeQueryConditions

from datetime import datetime


def createUser(telegram_id: int, phone: str) -> None:
    created_at: datetime = getCurrentDateTime()
    
    stmt = """
        INSERT INTO users
        (telegram_id, phone, created_at)
        VALUES (%s, %s, %s)
    """

    params = (telegram_id, phone, created_at)

    execute(stmt, params)


def getUser(user_id: int = None, telegram_id: int = None) -> dict | None:
    if (not user_id) and (not telegram_id):
        raise AttributeError("At least one argument must be passed")

    conditions_data: tuple = makeQueryConditions(id=user_id, telegram_id=telegram_id)
    conditions_string, conditions_params = conditions_data

    query = f"""
        SELECT id, telegram_id, phone, created_at
        FROM users
        {conditions_string}
    """

    response: list = fetch(query, conditions_params, fetch_type="one", as_dict=True)

    try:
        user: dict = response[0]
    except IndexError:
        user = None

    return user


def getUsers() -> list:
    query = "SELECT id, telegram_id, phone, created_at FROM users"
    users: list = fetch(query, fetch_type="all", as_dict=True)
    return users
