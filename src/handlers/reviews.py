import sys
sys.path.append("../") # src/

from access import access_checker
from exceptions import exceptions_catcher

from handlers.forms.add_review_form import start_add_review_form

from aiogram import Router, F
from aiogram.types import  CallbackQuery
from aiogram.fsm.context import FSMContext


router = Router(name=__name__)


@router.callback_query(F.data.endswith("add_review/"))
@exceptions_catcher()
@access_checker()
async def add_review(event: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await start_add_review_form(event, state)
