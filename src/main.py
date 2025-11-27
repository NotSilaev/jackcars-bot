from config import settings

from handlers import common, users, feedback, stats
from handlers.forms import add_user_form, add_feedback_request_form

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

import asyncio


async def main() -> None:
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Handlers routers
    dp.include_router(common.router)
    dp.include_router(users.router)
    dp.include_router(feedback.router)
    dp.include_router(stats.router)

    # Forms routers
    dp.include_router(add_user_form.router)
    dp.include_router(add_feedback_request_form.router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, RuntimeError):
        print("Bot has been stopped.")
