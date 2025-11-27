from aiogram.fsm.state import StatesGroup
from aiogram.fsm.context import FSMContext


async def makeFormStateMessage(states_group: StatesGroup, state: FSMContext) -> str:
    "Generates a message based on the current status values."

    form_state_items = []

    state_data: dict = await state.get_data()
    for key, value in state_data.items():
        if (not value) or (not value["value"]):
            continue
        state_title: str = states_group.titles[key]
        state_view: str = value["view"]
        form_state_items.append(f"{state_title}: *{state_view}*")

    form_state_message = "\n".join(form_state_items)
    return form_state_message
