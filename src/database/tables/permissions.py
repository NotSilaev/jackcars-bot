import sys
sys.path.append("../../") # src/

from database import fetch


def getRolePermissions(role_id: int) -> list:
    query = """
        SELECT p.id, p.slug, p.name
        FROM roles_permissions rp
        JOIN permissions p
            ON rp.permission_id = p.id
        WHERE rp.role_id = %s
    """
    params = (role_id, )

    permissions: list = fetch(query, params, fetch_type="all", as_dict=True)

    return permissions
