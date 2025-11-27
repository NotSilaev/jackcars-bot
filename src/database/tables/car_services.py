import sys
sys.path.append("../../") # src/

from database import fetch


def getCarServices() -> list:
    query = "SELECT id, slug, name FROM car_services"
    car_services: list = fetch(query, fetch_type="all", as_dict=True)
    return car_services


def getCarService(car_service_id: int) -> dict | None:
    query = """
        SELECT id, slug, name
        FROM car_services
        WHERE id = %s
    """

    params = (car_service_id, )

    response: list = fetch(query, params, fetch_type="one", as_dict=True)

    try:
        car_service: dict = response[0]
    except IndexError:
        car_service = None

    return car_service
