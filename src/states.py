from aiogram.types import Message, CallbackQuery


def getCurrentStateCallback(event: Message | CallbackQuery, show_params: bool = False) -> str | None:
    "Returns a callback of the current user state."

    if isinstance(event, Message):
        current_state_callback = None
    elif isinstance(event, CallbackQuery):
        current_state_callback: str = event.data

    if show_params is False:
        current_state_callback: str = current_state_callback.split("?")[0]

    return current_state_callback


def makeNextStateCallback(
    event_or_state_callback: Message | CallbackQuery | str, 
    next_state: str, 
    next_state_params: dict = None,
    is_start: bool = False
) -> str:
    "Generates a callback for the transition to the next state."

    if is_start:
        states_chain = ["start"]
    else:
        if isinstance(event_or_state_callback, str):
            states_chain: list = event_or_state_callback.rstrip("/").split("/")
        else:
            event: Message | CallbackQuery = event_or_state_callback
            if isinstance(event, Message):
                states_chain = []
            elif isinstance(event, CallbackQuery):
                states_chain: list = event.data.rstrip("/").split("/")

    states_chain.append(next_state + "/")

    if not next_state_params:
        next_state_callback = "/".join(states_chain)
    else:
        next_state_params_chain = []
        for param, value in next_state_params.items():
            next_state_params_chain.append(f"{param}={value}")
        next_state_callback = "/".join(states_chain) + "?" + "&".join(next_state_params_chain)

    return next_state_callback


def makePrevStateCallback(event: Message | CallbackQuery) -> str | None:
    "Generates a callback to return to the previous state."

    if not isinstance(event, CallbackQuery):
        return None

    state_callback: str = getCurrentStateCallback(event)

    states_chain: list = state_callback.rstrip("/").split("/")
    if len(states_chain) == 1:
        return None

    del states_chain[-1]
    prev_state_callback = "/".join(states_chain) + "/"

    return prev_state_callback

    
def updateStateCallbackParams(
    event_or_state_callback: Message | CallbackQuery | str,
    new_state_params: dict, 
    save_unchanged: bool = False
) -> str | None:
    """
    Generates a state callback with new parameters.
    
    :param new_state_params: dict of values of new or existing parameters.
    :param save_unchanged: if `True` does not delete parameters not specified in `new_state_params`.
    """

    if (
        isinstance(event_or_state_callback, Message) 
        or isinstance(event_or_state_callback, CallbackQuery)
    ):
        state_callback: str = getCurrentStateCallback(event)
        if not state_callback:
            return
    elif isinstance(event_or_state_callback, str):
        state_callback: str = event_or_state_callback

    state_callback_items: list = state_callback.split("?")
    state: str = state_callback_items[0]
    try:
        state_params: str = state_callback_items[1]
    except IndexError:
        state_params = None

    state_params_chain = []
    if state_params and save_unchanged:
        for i, params_item in state_params.split("&"):
            param, value = params_item.split("=")
            if param not in new_state_params.keys():
                state_params_chain.append(f"{param}={value}")

    for param, value in new_state_params.items():
        state_params_chain.append(f"{param}={value}")

    state_params = "&".join(state_params_chain)
    state_callback = state + "?" + state_params
    return state_callback
