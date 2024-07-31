#!/bin/bash

# Создаем виртуальное окружение
python3 -m venv venv

# Активируем виртуальное окружение
source venv/bin/activate

# Устанавливаем необходимые пакеты
pip3 install aiogram pydantic-settings sqlalchemy alembic aiosqlite

# Сохраняем установленные пакеты в requirements.txt
pip3 freeze > requirements.txt

# Создаем файл main.py и вставляем в него код
cat <<EOL > main.py
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.config import settings


TOKEN = settings.API_TOKEN

dp = Dispatcher()

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")


@dp.message()
async def echo_handler(message: Message) -> None:
    try:
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        await message.answer("Nice try!")


async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
EOL

# Создаем файл .env и вставляем в него код
cat <<EOL > .env
API_TOKEN=
DB_PATH=sqlite+aiosqlite:///database.db
EOL

# Создаем файл alembic.ini и вставляем в него код
alembic init alembic
cat <<EOL > alembic.ini
[alembic]

script_location = alembic
prepend_sys_path = .

version_path_separator = os

sqlalchemy.url = sqlite:///database.db


[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
EOL

# Редактируем файл alembic/env.py
cd alembic
cat <<EOL > env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

config = context.config

fileConfig(config.config_file_name)

from app.models import Base
target_metadata = Base.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is also acceptable
    here.  By skipping the Engine creation we don't even need a
    DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True  # Включите batch mode здесь
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
EOL

# Создаем директорию app и переходим в нее
mkdir app
cd app

# Создаем файл config.py и вставляем в него код
cat <<EOL > config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    API_TOKEN: str
    DB_PATH: str

    class Config:
        env_file = ".env"

settings = Settings()
EOL

# Создаем файл models.py и вставляем в него код
cat <<EOL > models.py
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()
EOL

# Инициализируем базу данных
cd ..
alembic revision -m "alembic initial"

echo "Проект успешно создан!"