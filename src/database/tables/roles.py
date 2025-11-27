import sys
sys.path.append("../../") # src/

from database import fetch
from database.utils import makeQueryConditions


def getRole(role_id: int = None, role_slug: str = None) -> dict | None:
    if (not role_id) and (not role_slug):
        raise AttributeError("At least one argument must be passed")

    conditions_data: tuple = makeQueryConditions(id=role_id, slug=f"'{role_slug}'")
    conditions_string, conditions_params = conditions_data

    query = f"""
        SELECT id, slug, name
        FROM roles
        {conditions_string}
    """

    response: list = fetch(query, conditions_params, fetch_type="one", as_dict=True)

    try:
        role: dict = response[0]
    except IndexError:
        role = None

    return role
