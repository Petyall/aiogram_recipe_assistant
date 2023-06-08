import logging

from config import settings
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from aiogram.dispatcher.filters import Command
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from pymongo import MongoClient


logging.basicConfig(level=logging.INFO)

# Replace xxx with your bot token
TOKEN = settings.API_TOKEN

# Initialize bot and dispatcher
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# Initialize MongoDB client
MONGODB_URL = settings.MONGODB_URL
client = MongoClient(MONGODB_URL)
db = client['cookie_bot']
collection = db.receipts


class AddArticle(StatesGroup):
    waiting_for_title = State()
    waiting_for_text = State()

@dp.message_handler(Command("start"))
async def start(message: types.Message):
    # Переходим к стадии ожидания названия статьи
    await message.answer("Чтобы пользоваться функциями, жми кнопку menu на экране.\nТам перечислен список основных команд, но навсякий случай расскажу тебе их здесь!\n/all - Вывод всех рецептов 🦑\n/get_receipt - Получить рецепт по названию 🔎\n/add- Добавить рецепт ✔️")

@dp.message_handler(Command("add"))
async def add_article(message: types.Message):
    # Переходим к стадии ожидания названия статьи
    await message.answer("Напиши название рецепта, чтобы я смог его запомнить")
    await AddArticle.waiting_for_title.set()

# С помощью декоратора message_handler обработчик сообщений добавится к стадии waiting_for_title
@dp.message_handler(state=AddArticle.waiting_for_title)
async def process_title(message: types.Message, state: FSMContext):
    # Сохраняем название статьи
    async with state.proxy() as data:
        data['title'] = message.text.lower()
    # Переходим к стадии ожидания текста статьи
    await message.answer(f"Отлично! Теперь, пожалуйста, введи пункты приготовления для рецепта '{data['title']}'")
    await AddArticle.waiting_for_text.set()

# С помощью декоратора message_handler обработчик сообщений добавится к стадии waiting_for_text
@dp.message_handler(state=AddArticle.waiting_for_text)
async def process_text(message: types.Message, state: FSMContext):
    # Сохраняем текст статьи
    async with state.proxy() as data:
        data['text'] = message.text
        db.receipts.insert_one({'user_id': message.from_user.id, 'title': data['title'], 'text': data['text']})
        # Формируем сообщение и отправляем его пользователю
        response = f"✅Рецепт '{data['title']}' успешно добавлен!✅\n\n{data['text']}"
        await message.answer(response)
    # Сбрасываем все состояния
    await state.finish()


class GetReceiptForm(StatesGroup):
    title = State()

@dp.message_handler(commands='get_receipt')
async def cmd_get_receipt(message: types.Message):
    await GetReceiptForm.title.set()
    await message.reply("Чтобы я нашел рецепт, напиши его название🕵🏻")

@dp.message_handler(state=GetReceiptForm.title)
async def process_get_receipt(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['title'] = message.text.lower()
        # проходим курсор в цикле и получаем записи из полей 'title' и 'text'
        receipts = db.receipts.find_one({'title': data['title']})
        if receipts:
            await message.reply('Вот что я нашел для тебя😊')
            # response = 'Вот что я нашел для тебя😊\n'
            response = f"{receipts['title'].upper()}:\n\n{receipts['text']}"
        else:
            response = 'К сожалению, я не знаю таких рецептов😔\nНо ты можешь стать первым(ой) и добавить его!'
        
        # отправляем ответ пользователю
        await message.answer(response)

    # завершаем диалог
    await state.finish()

@dp.message_handler(commands='all')
async def cmd_get_receipt(message: types.Message):
    await message.reply(f"Понял, вывожу все рецепты, которые знаю😊")
    response = ""
    for receipt in collection.find():
        response += f"📖{receipt['title'].upper()}📖\n\n"
        # await message.answer(f"📖РЕЦЕПТ {receipt['title'].upper()}📖\n{receipt['text']}")
    await message.answer(response)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)



# Добавление записей в БД
# post = {"author": "petyal",
#         "text": "My first blog post!"
# }
# collection_id = collection.insert_one(post).inserted_id
# collection_id

# Вывод записей из БД
# for i in collection.find():
#     print(i)