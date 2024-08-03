import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.config import settings
from app.handlers import recipes_router
from app.middlewares import WhitelistMiddleware

TOKEN = settings.API_TOKEN

dp = Dispatcher()
dp.message.middleware(WhitelistMiddleware())


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(
        f"Привет, {html.bold(message.from_user.full_name)}!\n\nЧтобы пользоваться функциями, жми кнопку menu на экране. Там перечислен список основных команд, но навсякий случай расскажу тебе их здесь!\n/add_recipe - Добавить рецепт 🦑\n/get_recipe - Получение рецепта 🔎"
    )


async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp.include_router(recipes_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
