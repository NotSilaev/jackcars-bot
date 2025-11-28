import sys
sys.path.append("../../") # src/

from utils.common import getCurrentDateTime

from database import execute, fetch
from database.utils import makeQueryConditions

from datetime import datetime


def createFeedbackRequest(
    user_id: int, 
    car_service_id: int, 
    employee_id: int, 
    contact_method_id: int, 
    request_reason: str
) -> None:
    created_at: datetime = getCurrentDateTime()

    stmt = """
        INSERT INTO feedback_requests
        (user_id, car_service_id, employee_id, contact_method_id, request_reason, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    """
    
    params = (user_id, car_service_id, employee_id, contact_method_id, request_reason, created_at)

    new_row: tuple = execute(stmt, params, returning=True)
    
    feedback_request_id: int = new_row[0]
    return feedback_request_id


def getFeedbackRequest(feedback_request_id: int) -> dict | None:
    query = """
        SELECT 
            id, user_id, car_service_id, 
            employee_id, contact_method_id, 
            request_reason, taken_at, 
            completed_at, created_at
        FROM 
            feedback_requests
        WHERE 
            id = %s
    """

    params = (feedback_request_id, )

    response: list = fetch(query, params, fetch_type="one", as_dict=True)

    try:
        feedback_request: dict = response[0]
    except IndexError:
        feedback_request = None

    return feedback_request


def getFeedbackRequests(
    user_id: int = None, 
    car_service_id: int = None, 
    employee_id: int = None, 
    contact_method_id: int = None,
    completed_at_is_null: bool = False
) -> list:
    conditions_data: tuple = makeQueryConditions(
        null_columns=(("completed_at", ) if completed_at_is_null else None),
        user_id=user_id, 
        car_service_id=car_service_id,
        employee_id=employee_id,
        contact_method_id=contact_method_id
    )
    conditions_string, conditions_params = conditions_data

    query = f"""
        SELECT 
            id, user_id, car_service_id, 
            employee_id, contact_method_id, 
            request_reason, taken_at, 
            completed_at, created_at
        FROM 
            feedback_requests
        {conditions_string}
    """

    feedback_requests: list = fetch(query, conditions_params, fetch_type="all", as_dict=True)

    return feedback_requests


def getLastUserFeedbackRequest(user_id: int) -> dict | None:
    query = """
        SELECT 
            id, user_id, car_service_id, 
            employee_id, contact_method_id, 
            request_reason, taken_at, 
            completed_at, created_at
        FROM 
            feedback_requests
        WHERE 
            user_id = %s
        ORDER BY 
            created_at DESC 
        LIMIT 1
    """

    params = (user_id, )

    response: list = fetch(query, params, fetch_type="one", as_dict=True)

    try:
        feedback_request: dict = response[0]
    except IndexError:
        feedback_request = None

    return feedback_request


def setFeedbackRequestTaken(feedback_request_id: int, employee_id: int) -> None:
    taken_at: datetime = getCurrentDateTime()

    stmt = """
        UPDATE feedback_requests
        SET employee_id = %s, taken_at = %s
        WHERE id = %s
    """
    
    params = (employee_id, taken_at, feedback_request_id)

    execute(stmt, params)


def setFeedbackRequestCompleted(feedback_request_id: int) -> None:
    completed_at: datetime = getCurrentDateTime()

    stmt = """
        UPDATE feedback_requests
        SET completed_at = %s
        WHERE id = %s
    """
    
    params = (completed_at, feedback_request_id)

    execute(stmt, params)
