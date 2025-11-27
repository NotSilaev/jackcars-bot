import sys
sys.path.append("../") # src/

from config import settings

import psycopg2
from typing import Any


def getDatabaseConnection() -> psycopg2.extensions.connection:
    return psycopg2.connect(
        host=settings.DB_HOST, 
        port=settings.DB_PORT,
        dbname=settings.DB_NAME, 
        user=settings.DB_USER,
        password=settings.DB_PASSWORD, 
    )


def execute(stmt: str, params: tuple, returning: bool = False) -> None | Any:
    """
    Executes an SQL statement query.
    
    :param stmt: SQL statement query.
    :param returning: set to `True` if the sql query contains the `RETURNING` statement.
    """

    with getDatabaseConnection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(stmt, params)
            if returning:
                new_row: tuple = cursor.fetchone()
                return new_row


def fetch(query: str, params: tuple = None, fetch_type: str = "one", as_dict: bool = False) -> list:
    """
    Executes an SQL fetch query.
    
    :param query: SQL fetch query.
    :param fetch_type: if `one`, the fetchone() function will be executed, if `all` - the fetchall().
    :param as_dict: if `True`, returns the response in the dictionary view.
    """

    with getDatabaseConnection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)

            match fetch_type:
                case "one": response = cursor.fetchone()
                case "all": response = cursor.fetchall()
                case _:
                    raise ValueError("Invalid fetch_type")

    if not response:
        response = list()

    if as_dict and response:
        columns = [desk[0] for desk in cursor.description]
        match fetch_type:
            case "one":
                response = [dict(zip(columns, response))]
            case "all":
                response = [dict(zip(columns, row)) for row in response]

    return response
