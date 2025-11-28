import sys
sys.path.append("../") # src/

from states import updateStateCallbackParams

from aiogram.utils.keyboard import InlineKeyboardBuilder

import math


class Paginator:
    def __init__(self, array: list|tuple, offset: int, page_callback: str, back_callback: str = None) -> None:
        self.array = array
        self.offset = offset
        self.pages_count = math.ceil(len(array) / offset)
        self.page_callback = page_callback
        self.back_callback = back_callback

    def makePageKeyboard(self, page: int) -> InlineKeyboardBuilder:
        "Creates a pagination keyboard for the required page."

        if page > self.pages_count:
            raise ValueError(
                f"Page number value cannot be higher than pages count [page: {page} / {self.pages_count}]."
            )

        start_index =  self.offset * (page - 1)
        end_index = start_index + self.offset
        array_items = self.array[start_index:end_index]
        array_items_count = len(array_items)
        
        keyboard = InlineKeyboardBuilder()

        if array_items_count > 0:
            for item in array_items:
                keyboard.button(text=item["text"], callback_data=item["callback_data"])

            if self.pages_count > 1:
                if page != 1:
                    keyboard.button(
                        text="⬅️", 
                        callback_data=updateStateCallbackParams(
                            event_or_state_callback=self.page_callback, 
                            new_state_params={"page": page-1},
                            save_unchanged=True
                        )
                    )
                else:
                    keyboard.button(text="🚩", callback_data="#")

                keyboard.button(text=f"{page} / {self.pages_count}", callback_data="#")

                if page != self.pages_count:
                    keyboard.button(
                        text="➡️", 
                        callback_data=updateStateCallbackParams(
                            event_or_state_callback=self.page_callback, 
                            new_state_params={"page": page+1},
                            save_unchanged=True
                        )
                    )
                else:
                    keyboard.button(text="🏁", callback_data="#")

            if self.back_callback:
                keyboard.button(text="⬅️ Назад", callback_data=self.back_callback)

            items_rows = "1," * array_items_count
            exec(f"keyboard.adjust({items_rows} 3, 1)")

        return keyboard
