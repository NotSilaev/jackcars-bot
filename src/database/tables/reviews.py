import sys
sys.path.append("../../") # src/

from utils.common import getCurrentDateTime

from database import execute, fetch
from database.utils import makeQueryConditions

from datetime import datetime


def createReview(user_id: int, car_service_id: int, text: str, rating: int) -> None:
    created_at: datetime = getCurrentDateTime()

    stmt = """
        INSERT INTO reviews
        (user_id, car_service_id, text, rating, created_at)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """
    
    params = (user_id, car_service_id, text, rating, created_at)

    new_row: tuple = execute(stmt, params, returning=True)
    
    review_id: int = new_row[0]
    return review_id


def getReview(review_id: int) -> dict | None:
    query = """
        SELECT id, user_id, car_service_id, text, rating, created_at
        FROM reviews
        WHERE id = %s
    """

    params = (review_id, )

    response: list = fetch(query, params, fetch_type="one", as_dict=True)

    try:
        review: dict = response[0]
    except IndexError:
        review = None

    return review


def getUserReviews(user_id: int) -> list:
    query = f"""
        SELECT id, user_id, car_service_id, text, rating, created_at
        FROM reviews
        WHERE user_id = %s
    """

    params = (user_id, )

    user_reviews: list = fetch(query, params, fetch_type="all", as_dict=True)

    return user_reviews
