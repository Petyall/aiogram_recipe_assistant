from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from aiogram.dispatcher.filters import Command
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bson import ObjectId
from pymongo import MongoClient
from logging import basicConfig, INFO

from config import settings


basicConfig(level=INFO)

# Подключение бота
TOKEN = settings.API_TOKEN
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# Подключение MongoDB
MONGODB_URL = settings.MONGODB_URL
client = MongoClient(MONGODB_URL)
db = client['cookie_bot']
collection = db.receipts

# Класс для машины состояний с добавлением рецептов
class AddReceipt(StatesGroup):
    waiting_for_title = State()
    waiting_for_text = State()


# Функция обработки команды /start
@dp.message_handler(Command("start"))
async def start(message: types.Message):
    # Ответ пользователю
    await message.answer("Чтобы пользоваться функциями, жми кнопку menu на экране.\nТам перечислен список основных команд, но навсякий случай расскажу тебе их здесь!\n/all - Вывод всех рецептов 🦑\n/get_receipt - Получить рецепт по названию 🔎\n/add- Добавить рецепт ✔️")


# Функция обработки команды /add
@dp.message_handler(Command("add"))
async def add_article(message: types.Message):
    # Ответ пользователю
    await message.answer("Напиши название рецепта, чтобы я смог его запомнить")
    # Переход к стадии ожидания названия рецепта от пользователя
    await AddReceipt.waiting_for_title.set()


# Функция обработки состояния waiting_for_title
@dp.message_handler(state=AddReceipt.waiting_for_title)
async def process_title(message: types.Message, state: FSMContext):
    # Сохранение названия рецепта в локальное хранилище
    async with state.proxy() as data:
        # Получение названия рецепта из сообщения пользователя
        data['title'] = message.text.lower()
    # Ответ пользователю
    await message.answer(f"Отлично! Теперь, пожалуйста, введи пункты приготовления для рецепта '{data['title']}'")
    # Переход к стадии ожидания рецепта от пользователя
    await AddReceipt.waiting_for_text.set()


# Функция обработки состояния waiting_for_text
@dp.message_handler(state=AddReceipt.waiting_for_text)
async def process_text(message: types.Message, state: FSMContext):
    # Сохранение рецепта в локальное хранилище
    async with state.proxy() as data:
        # Получение рецепта из сообщения пользователя
        data['text'] = message.text
        # Соххранение рецепта в БД
        db.receipts.insert_one({'user_id': message.from_user.id, 'title': data['title'], 'text': data['text']})
        # Ответ пользователю
        await message.answer(f"✅Рецепт '{data['title']}' успешно добавлен!✅\n\n{data['text']}")
    # Завершение и сброс всех состояний
    await state.finish()


# Класс для машины состояний с поиском рецептов
class GetReceiptForm(StatesGroup):
    title = State()


# Функция обработки команды /get_receipt
@dp.message_handler(commands='get_receipt')
async def cmd_get_receipt(message: types.Message):
    # Ответ пользователю
    await message.reply("Чтобы я нашел рецепт, напиши его название🕵🏻")
    # Переход к стадии ожидания названия рецепта от пользователя
    await GetReceiptForm.title.set()


# Функция обработки состояния title
@dp.message_handler(state=GetReceiptForm.title)
async def process_get_receipt(message: types.Message, state: FSMContext):
    # Сохранение названия рецепта в локальное хранилище
    async with state.proxy() as data:
        # Получение названия рецепта из сообщения пользователя
        data['title'] = message.text.lower()
        # Поиск рецепта в БД
        receipts = db.receipts.find_one({'title': data['title']})
        # Создание положительного ответа, если рецепт существует
        if receipts:
            # Ответ пользователю
            await message.reply('Вот что я нашел для тебя😊')
            response = f"{receipts['title'].upper()}:\n\n{receipts['text']}"
        # Создание отрицательного ответа, если рецепт не существует
        else:
            # Ответ пользователю
            response = 'К сожалению, я не знаю таких рецептов😔\nНо ты можешь стать первым(ой) и добавить его!'
        # Отправление ответа пользователю
        await message.answer(response)
    # Завершение и сброс всех состояний
    await state.finish()


# # Функция обработки команды /all
# @dp.message_handler(commands='all')
# async def cmd_all(message: types.Message):
#     # Ответ пользователю
#     await message.reply(f"Понял, вывожу все рецепты, которые знаю😊")
#     response = ""
#     # Вывод всех рецептов
#     for receipt in collection.find():
#         response += f"📖{receipt['title'].upper()}📖\n\n"
#     # Ответ пользователю
#     await message.answer(response)


# @dp.message_handler(commands='b1')
# async def button1(message: types.Message):
#     markup = InlineKeyboardMarkup()
#     button = InlineKeyboardButton(text='pip', callback_data='butt_id')
#     markup.add(button)

#     await bot.send_message(message.chat.id, 'message text', reply_markup=markup)

# @dp.callback_query_handler(lambda c: c.data == 'butt_id')
# async def to_query(call: types.callback_query):
#     await bot.answer_callback_query(call.id)
#     await bot.send_message(call.message.chat.id, 'button pressed')


# @dp.message_handler(commands='b1')
# async def button1(message: types.Message):
#     markup = InlineKeyboardMarkup()
#     for receipt in collection.find():
#         button = InlineKeyboardButton(text=f"📖{receipt['title'].upper()}📖", callback_data='butt_id')
#         markup.add(button)

#     await bot.send_message(message.chat.id, 'Понял, вывожу все рецепты, которые знаю😊', reply_markup=markup)

# @dp.callback_query_handler(lambda c: c.data == 'butt_id')
# async def to_query(call: types.callback_query):
#     await bot.answer_callback_query(call.id)
#     await bot.send_message(call.message.chat.id, 'button pressed')













# from aiogram.utils.callback_data import CallbackData
# from bson.objectid import ObjectId

# button_callback = CallbackData('receipt', 'receipt_id')

# @dp.message_handler(commands='b1')
# async def button1(message: types.Message):
    
#     markup = InlineKeyboardMarkup()
#     for receipt in collection.find():
#         markup.add(InlineKeyboardButton(text=f"📖{receipt['title'].upper()}📖", callback_data=str(receipt['_id'])))

#     await bot.send_message(message.chat.id, 'Понял, вывожу все рецепты, которые знаю😊', reply_markup=markup)


from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

@dp.message_handler(commands='all')
async def start_handler(message: types.Message):
    keyboard = InlineKeyboardMarkup()
    
    for receipt in collection.find():
        button = InlineKeyboardButton(text=f"📖{receipt['title'].upper()}📖", callback_data=f"recipe_{receipt['_id']}")
        keyboard.add(button)
    
    await message.answer("Понял, вывожу все рецепты, которые знаю😊", reply_markup=keyboard)

@dp.callback_query_handler()
async def recipe_handler(call: types.callback_query):
    recipe_id = call.data.split("_")[1]
    recipe = db.receipts.find_one({"_id": ObjectId(recipe_id)})
    await bot.send_message(call.message.chat.id, f'📖{recipe["title"].upper()}📖\n\n{recipe["text"]}')



if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
