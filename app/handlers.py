from aiogram import html, types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.keyboards import add_recipe_cancel_keyboard, add_recipe_get_recipe_categories_keyboard, get_recipe_cancel_keyboard, get_recipe_get_recipe_categories_keyboard, get_recipe_get_recipes_keyboard
from app.states import AddRecipeStates, GetRecipeStates
from app.requests import RecipeRequests, CategoryRequests, UserRequests


recipes_router = Router()


@recipes_router.message(Command("add_recipe"))
async def cmd_add_recipe(message: types.Message, state: FSMContext):
    await state.set_state(AddRecipeStates.SELECT_CATEGORY)
    keyboard = await add_recipe_get_recipe_categories_keyboard()
    await message.reply(f"Выберите {html.bold('категорию')} нового рецепта 🧑‍🍳", reply_markup=keyboard)


@recipes_router.callback_query(lambda c: c.data.startswith('category_'), AddRecipeStates.SELECT_CATEGORY)
async def add_recipe_process_select_category(callback_query: types.CallbackQuery, state: FSMContext):
    category_id = int(callback_query.data.split('_')[1])
    selected_category = await CategoryRequests.find_one_or_none(id=category_id)
    await state.update_data(recipe_category=selected_category.id)
    await state.set_state(AddRecipeStates.GET_ARTICLE)
    keyboard = add_recipe_cancel_keyboard()
    await callback_query.bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id,
                                text=f"Понял, Вы хотите добавить {selected_category.name.lower()}. Введите {html.bold('название')} рецепта:",
                                reply_markup=keyboard)


@recipes_router.message(F.text, AddRecipeStates.GET_ARTICLE)
async def add_recipe_process_get_article(message: types.Message, state: FSMContext):
    recipe_article = message.text
    await state.update_data(recipe_article=recipe_article)
    await state.set_state(AddRecipeStates.GET_INGREDIENTS)
    keyboard = add_recipe_cancel_keyboard()
    await message.reply(text=f"Отлично! Теперь введите {html.bold('ингридиенты')} рецепта:", reply_markup=keyboard)


@recipes_router.message(F.text, AddRecipeStates.GET_INGREDIENTS)
async def add_recipe_process_get_ingredients(message: types.Message, state: FSMContext):
    recipe_ingredients = message.text
    await state.update_data(recipe_ingredients=recipe_ingredients)
    await state.set_state(AddRecipeStates.GET_STEPS)
    keyboard = add_recipe_cancel_keyboard()
    await message.reply(text=f"Остался последний пункт! Введите {html.bold('шаги')} рецепта:", reply_markup=keyboard)


@recipes_router.message(F.text, AddRecipeStates.GET_STEPS)
async def add_recipe_process_get_steps(message: types.Message, state: FSMContext):
    data = await state.get_data()
    recipe_article = data['recipe_article']
    recipe_ingredients = data['recipe_ingredients']
    recipe_category = data['recipe_category']
    recipe_steps = message.text

    user_id = message.from_user.id
    user = await UserRequests.find_one_or_none(id=user_id)
    if not user:
        await UserRequests.add(id=user_id, username=message.from_user.username)
        user = await UserRequests.find_one_or_none(id=user_id)
    recipe_created_by = user.id

    await RecipeRequests.add(article=recipe_article, ingredients=recipe_ingredients, steps=recipe_steps, category_id=recipe_category, created_by_id=recipe_created_by)
    await state.clear()
    await message.reply(text=f"Супер! Теперь я знаю рецепт {html.bold(recipe_article)}")


@recipes_router.callback_query(lambda c: c.data == 'cancel_adding_recipe')
async def add_recipe_process_cancel(callback_query: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback_query.bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id,
                                text="Добавление рецепта завершено")
    


@recipes_router.message(Command("get_recipe"))
async def cmd_get_recipe(message: types.Message, state: FSMContext):
    await state.set_state(GetRecipeStates.SELECT_CATEGORY)
    keyboard = await get_recipe_get_recipe_categories_keyboard()
    await message.reply(f"Выберите {html.bold('категорию')} рецепта 🧑‍🍳", reply_markup=keyboard)


@recipes_router.callback_query(lambda c: c.data.startswith('category_'), GetRecipeStates.SELECT_CATEGORY)
async def get_recipe_process_select_category(callback_query: types.CallbackQuery, state: FSMContext):
    category_id = int(callback_query.data.split('_')[1])
    selected_category = await CategoryRequests.find_one_or_none(id=category_id)

    await state.update_data(recipe_category=selected_category.id)
    await state.set_state(GetRecipeStates.SELECT_RECIPE)
    
    keyboard = await get_recipe_get_recipes_keyboard(category_id)
    await callback_query.bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id,
                                text=f"Выберите нужный рецепт:",
                                reply_markup=keyboard)
    

@recipes_router.callback_query(lambda c: c.data.startswith('recipe_'), GetRecipeStates.SELECT_RECIPE)
async def get_recipe_process_select_recipe(callback_query: types.CallbackQuery, state: FSMContext):
    recipe_id = int(callback_query.data.split('_')[1])
    selected_recipe = await RecipeRequests.find_one_or_none(id=recipe_id)

    # await state.update_data(recipe_category=selected_category.id)
    # await state.set_state(GetRecipeStates.SELECT_RECIPE)
    
    keyboard = get_recipe_cancel_keyboard()
    await callback_query.bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id,
                                text=f"{selected_recipe.article}\n\n{selected_recipe.ingredients}\n\n{selected_recipe.steps}",
                                reply_markup=keyboard)
    

@recipes_router.callback_query(lambda c: c.data == 'cancel_getting_recipe')
async def get_recipe_process_cancel(callback_query: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback_query.bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id,
                                text="Просмотр рецепта завершен")


@recipes_router.callback_query(lambda c: c.data == 'back_to_recipes')
async def get_recipe_process_back_to_recipes(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    category_id = data['recipe_category']

    await state.set_state(GetRecipeStates.SELECT_RECIPE)

    keyboard = await get_recipe_get_recipes_keyboard(category_id)
    await callback_query.bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id,
                                text=f"Выберите нужный рецепт:",
                                reply_markup=keyboard)
    
@recipes_router.callback_query(lambda c: c.data == 'back_to_categories')
async def get_recipe_process_back_to_categories(callback_query: types.CallbackQuery, state: FSMContext):

    await state.set_state(GetRecipeStates.SELECT_CATEGORY)

    keyboard = await get_recipe_get_recipe_categories_keyboard()
    await callback_query.bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id,
                                text=f"Выберите {html.bold('категорию')} рецепта 🧑‍🍳",
                                reply_markup=keyboard)