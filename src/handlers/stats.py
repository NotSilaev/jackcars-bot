import sys
sys.path.append("../") # src/

from access import access_checker
from exceptions import exceptions_catcher
from states import makeNextStateCallback, makePrevStateCallback
from utils.common import respondEvent, getCallParams, makePeriodDatetimes
from utils.keyboard import makeItemsKeyboard

from modules.stats import STATS_BLOCKS, StatsBlock, getStatsBlock

from aiogram import Router, F
from aiogram.types import  CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from aiogram.fsm.context import FSMContext


router = Router(name=__name__)


@router.callback_query(F.data.split("?")[0].endswith("stats/"))
@exceptions_catcher()
@access_checker(required_permissions=["get_stats"])
async def stats(event: CallbackQuery, state: FSMContext) -> None:
    await state.clear()

    call_params: dict = getCallParams(event)

    if "block_id" in call_params:
        stats_block_id: str = call_params["block_id"]

        try:
            period_id: str = call_params["period_id"]
            period: tuple = makePeriodDatetimes(period_id)
        except KeyError:
            period = None

        stats_block: StatsBlock = getStatsBlock(block_id=stats_block_id)
        stats_block = stats_block(event=event, period=period)
        message_text = stats_block.makeText()
        keyboard: InlineKeyboardBuilder = stats_block.makeKeyboard()

    else:
        message_text = (
            f"*📊 Статистика*" + "\n\n"
            + "🗃 Выберите необходимый блок статистики"
        )
        items_buttons = []
        for block_id, block_data in STATS_BLOCKS.items():
            items_buttons.append({
                "text": block_data["name"], 
                "callback_data": makeNextStateCallback(event, "stats", next_state_params={"block_id": block_id})
            })
        keyboard = makeItemsKeyboard(items_buttons, row_length=2)

    if prev_state := makePrevStateCallback(event):
        keyboard.row(InlineKeyboardButton(text="⬅️ Назад", callback_data=prev_state))

    await respondEvent(
        event,
        text=message_text, 
        parse_mode="Markdown",
        reply_markup=keyboard.as_markup()
    )
