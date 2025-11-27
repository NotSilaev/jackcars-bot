def shortenFullanme(fullname: str) -> str:
    "Abbreviates the full name to the full family name and the first letters of the first name and patronymic."

    parts = fullname.strip().split()
    if len(parts) < 2:
        return fullname
    
    last_name = parts[0]
    first_initial = parts[1][0].upper() + '.'
    middle_initial = parts[2][0].upper() + '.' if len(parts) > 2 else ''
    
    return f"{last_name} {first_initial} {middle_initial}".strip()
