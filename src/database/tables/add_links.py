import sys
sys.path.append("../../") # src/

from utils.common import getCurrentDateTime

from database import execute, fetch

from datetime import datetime
import json


def createAddLink(add_link_id: str, employee_id: int, data: dict, activations_limit: int = 1):
    activations = 0
    data = json.dumps(data)
    created_at: datetime = getCurrentDateTime()

    stmt = """
        INSERT INTO add_links
        (id, employee_id, data, activations, activations_limit, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    params = (add_link_id, employee_id, data, activations, activations_limit, created_at)

    execute(stmt, params)


def getAddLink(add_link_id: str) -> dict | None:
    query = """
        SELECT id, employee_id, data, activations, activations_limit, created_at
        FROM add_links
        WHERE id = %s
    """

    params = (add_link_id, )

    response: list = fetch(query, params, fetch_type="one", as_dict=True)

    try:
        add_link: dict = response[0]
    except IndexError:
        add_link = None

    return add_link


def getAddLinks() -> list:
    query = """
        SELECT id, employee_id, data, activations, activations_limit, created_at
        FROM add_links
    """

    add_links: list = fetch(query, fetch_type="all", as_dict=True)

    return add_links


def increaseAddLinkActivations(add_link_id: str) -> None:
    stmt = """
        UPDATE add_links
        SET activations = activations + 1
        WHERE id = %s
    """

    params = (add_link_id, )

    execute(stmt, params)
