from aiogram import BaseMiddleware, types

from app.config import settings
from app.handlers import UserRequests


class AccessDeniedException(Exception):
    """Класс исключения, возникающего при попытке обращения к боту без white листа"""

    pass


class WhitelistMiddleware(BaseMiddleware):
    """Middleware для проверки наличия пользователя в white листе"""

    def __init__(self):
        # Инициализация white листа
        super().__init__()
        self.whitelist = []

    async def get_users(self):
        """Метод получения списка telegram ID пользователей из базы данных"""
        users = await UserRequests.find_all()
        return [user.username for user in users]

    async def setup_whitelist(self):
        """Метод добавления пользователей в white лист"""
        self.whitelist = await self.get_users()

    async def refresh_whitelist(self):
        """Метод обновления white листа"""
        self.whitelist = await self.get_users()

    async def __call__(self, handler, event, data):
        """Метод проверки наличия пользователя в white листе"""
        await self.refresh_whitelist()

        username = event.from_user.username if isinstance(event, types.Message) else None
        if username and username not in self.whitelist and username != settings.ADMIN_ID:
            raise AccessDeniedException(f"Пользователя {username} нет в вайт-листе")
        return await handler(event, data)