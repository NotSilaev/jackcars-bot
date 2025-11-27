import sys
sys.path.append("../../") # src/

from database import fetch


def getContactMethods() -> list:
    query = "SELECT id, slug, name FROM contact_methods"
    contact_methods: list = fetch(query, fetch_type="all", as_dict=True)
    return contact_methods


def getContactMethod(contact_method_id: int) -> dict | None:
    query = """
        SELECT id, slug, name
        FROM contact_methods
        WHERE id = %s
    """

    params = (contact_method_id, )

    response: list = fetch(query, params, fetch_type="one", as_dict=True)

    try:
        contact_method: dict = response[0]
    except IndexError:
        contact_method = None

    return contact_method
