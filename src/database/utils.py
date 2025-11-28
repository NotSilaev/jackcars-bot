def makeQueryConditions(
    operator: str = "WHERE", 
    params_count: int = None, 
    null_columns: tuple = None,
    **kwargs
) -> tuple[str, tuple]:
    """
    Generates a string with sql query conditions and a tuple of parameters values.
    
    :param operator: `WHERE` is for standard conditions, `HAVING` is for aggregated conditions.
    :param **kwargs: column names and their values.
    """

    conditions = []

    if null_columns:
        for column in null_columns:
            conditions.append(f"{column} IS NULL")

    for key, value in kwargs.items():
        if not value:
            continue
        conditions.append(f"{key} = {value}")

    if conditions:
        conditions_count = len(conditions)
        if conditions_count > 1:
            where_string = " AND ".join(conditions)
        else:
            where_string: str = conditions[0]
        where_string = f"{operator.upper()} {where_string}"
        if not params_count:
            params_count: int = conditions_count
        params = ("%s" for i in range(0, params_count))
    else:
        where_string = ""; params = tuple()

    conditions_data = (where_string, params)
    return conditions_data
