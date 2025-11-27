from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton


def makeKeyboardRow(items: list) -> list:
    return [InlineKeyboardButton(text=item["text"], callback_data=item["callback_data"]) for item in items]


def makeItemsKeyboard(
    items_buttons: list[dict], 
    nav_buttons: list[dict] = None, 
    row_length: int = 1
) -> InlineKeyboardBuilder:
    "Generates an inline keyboard with an even distribution of list items along the lines."

    keyboard = InlineKeyboardBuilder()

    for i in range(0, len(items_buttons), row_length):
        row_items = items_buttons[i:i+2]
        keyboard.row(*makeKeyboardRow(row_items))

    if nav_buttons:
        keyboard.row(*makeKeyboardRow(nav_buttons))

    return keyboard
