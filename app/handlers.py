from aiogram import html, types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from app.keyboards import add_recipe_cancel_keyboard, add_recipe_get_recipe_categories_keyboard, get_recipe_cancel_keyboard, get_recipe_confirm_deletion_keyboard, get_recipe_confirm_edit_keyboard, get_recipe_edit_recipe_keyboard, get_recipe_get_recipe_categories_keyboard, get_recipe_get_recipes_keyboard
from app.states import AddRecipeStates, GetRecipeStates
from app.requests import RecipeRequests, CategoryRequests, UserRequests


recipes_router = Router()


@recipes_router.message(Command("add_recipe"))
async def cmd_add_recipe(message: types.Message, state: FSMContext):
    await state.set_state(AddRecipeStates.SELECT_CATEGORY)
    keyboard = await add_recipe_get_recipe_categories_keyboard()
    await message.reply(
        text=f"Выберите {html.bold('категорию')} нового рецепта", 
        reply_markup=keyboard
    )


@recipes_router.callback_query(lambda c: c.data.startswith('category_'), AddRecipeStates.SELECT_CATEGORY)
async def add_recipe_process_select_category(callback_query: types.CallbackQuery, state: FSMContext):
    category_id = int(callback_query.data.split('_')[1])
    selected_category = await CategoryRequests.find_one_or_none(id=category_id)
    await state.update_data(recipe_category=selected_category.id)
    await state.set_state(AddRecipeStates.GET_ARTICLE)
    keyboard = add_recipe_cancel_keyboard()
    message = await callback_query.bot.edit_message_text(
        chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id,
        text=(
            f"Понял, Вы хотите добавить {selected_category.name.lower()}. " 
            f"Введите {html.bold('название')} рецепта:"
        ),
        reply_markup=keyboard
    )
    await state.update_data(message_id=message.message_id)


@recipes_router.message(F.text, AddRecipeStates.GET_ARTICLE)
async def add_recipe_process_get_article(message: types.Message, state: FSMContext):
    recipe_article = message.text
    await state.update_data(recipe_article=recipe_article)
    await state.set_state(AddRecipeStates.GET_INGREDIENTS)

    data = await state.get_data()
    if 'message_id' in data:
        await message.bot.edit_message_reply_markup(
            chat_id=message.from_user.id, 
            message_id=data['message_id'], reply_markup=None
        )

    keyboard = add_recipe_cancel_keyboard()
    new_message = await message.reply(
        text=f"Отлично! Теперь введите {html.bold('ингридиенты')} рецепта:", 
        reply_markup=keyboard
    )
    await state.update_data(message_id=new_message.message_id)


@recipes_router.message(F.text, AddRecipeStates.GET_INGREDIENTS)
async def add_recipe_process_get_ingredients(message: types.Message, state: FSMContext):
    recipe_ingredients = message.text
    await state.update_data(recipe_ingredients=recipe_ingredients)
    await state.set_state(AddRecipeStates.GET_STEPS)

    data = await state.get_data()
    if 'message_id' in data:
        await message.bot.edit_message_reply_markup(
            chat_id=message.from_user.id, 
            message_id=data['message_id'], reply_markup=None
        )

    keyboard = add_recipe_cancel_keyboard()
    new_message =await message.reply(
        text=f"Остался последний пункт! Введите {html.bold('шаги')} рецепта:", 
        reply_markup=keyboard
    )
    await state.update_data(message_id=new_message.message_id)


@recipes_router.message(F.text, AddRecipeStates.GET_STEPS)
async def add_recipe_process_get_steps(message: types.Message, state: FSMContext):
    data = await state.get_data()
    recipe_article = data['recipe_article']
    recipe_ingredients = data['recipe_ingredients']
    recipe_category = data['recipe_category']
    recipe_steps = message.text

    username = message.from_user.username
    user = await UserRequests.find_one_or_none(username=username)
    if user:
        await UserRequests.update(username=username, id=message.from_user.id)
        # user = await UserRequests.find_one_or_none(id=message.from_user.id)
    recipe_created_by = user.id

    await RecipeRequests.add(
        article=recipe_article, 
        ingredients=recipe_ingredients, 
        steps=recipe_steps, 
        category_id=recipe_category, 
        created_by_id=recipe_created_by
    )

    await state.clear()
    await message.reply(text=f"Супер! Теперь я знаю рецепт {html.bold(recipe_article)}")
    await message.answer_sticker(sticker="CAACAgIAAxkBAAEHalZmreLHu9xcSQsIvVNst2SDKXKrBwAC6jYAAlzHwEojRC8Od4h7-DUE")


@recipes_router.callback_query(lambda c: c.data == 'cancel_adding_recipe')
async def add_recipe_process_cancel(callback_query: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback_query.bot.edit_message_text(
        chat_id=callback_query.from_user.id, 
        message_id=callback_query.message.message_id,
        text="Добавление рецепта завершено"
    )
    






@recipes_router.message(Command("get_recipe"))
async def cmd_get_recipe(message: types.Message, state: FSMContext):
    await state.set_state(GetRecipeStates.SELECT_CATEGORY)
    keyboard = await get_recipe_get_recipe_categories_keyboard()
    await message.reply(f"Выберите {html.bold('категорию')} рецепта", reply_markup=keyboard)


@recipes_router.callback_query(lambda c: c.data.startswith('category_'), GetRecipeStates.SELECT_CATEGORY)
async def get_recipe_process_select_category(callback_query: types.CallbackQuery, state: FSMContext):
    category_id = int(callback_query.data.split('_')[1])
    selected_category = await CategoryRequests.find_one_or_none(id=category_id)

    await state.update_data(recipe_category=selected_category.id)
    await state.set_state(GetRecipeStates.SELECT_RECIPE)

    keyboard = await get_recipe_get_recipes_keyboard(category_id)
    await callback_query.bot.edit_message_text(
        chat_id=callback_query.from_user.id, 
        message_id=callback_query.message.message_id,
        text=f"Выберите нужный рецепт:",
        reply_markup=keyboard
    )


@recipes_router.callback_query(lambda c: c.data.startswith('recipe_'), GetRecipeStates.SELECT_RECIPE)
async def get_recipe_process_select_recipe(callback_query: types.CallbackQuery, state: FSMContext):
    recipe_id = int(callback_query.data.split('_')[1])
    await state.update_data(recipe_id=recipe_id)
    selected_recipe = await RecipeRequests.find_one_or_none(id=recipe_id)
    recipe_created_by = await UserRequests.find_one_or_none(id=selected_recipe.created_by_id)

    is_author = selected_recipe.created_by_id == callback_query.from_user.id
    keyboard = get_recipe_cancel_keyboard(is_author)
    await callback_query.bot.edit_message_text(
        chat_id=callback_query.from_user.id, 
        message_id=callback_query.message.message_id,
        text=(
            f"{html.bold(selected_recipe.article)}\n\n"
            f"Ингридиенты:\n{selected_recipe.ingredients}\n\n"
            f"{selected_recipe.steps}\n\n"
            f"Создан пользователем @{recipe_created_by.username}"
        ),
        reply_markup=keyboard
    )


@recipes_router.callback_query(lambda c: c.data == 'cancel_getting_recipe')
async def get_recipe_process_cancel(callback_query: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback_query.bot.edit_message_text(
        chat_id=callback_query.from_user.id, 
        message_id=callback_query.message.message_id,
        text="Просмотр рецепта завершен"
    )


@recipes_router.callback_query(lambda c: c.data == 'back_to_recipes')
async def get_recipe_process_back_to_recipes(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    category_id = data['recipe_category']

    await state.set_state(GetRecipeStates.SELECT_RECIPE)

    keyboard = await get_recipe_get_recipes_keyboard(category_id)
    await callback_query.bot.edit_message_text(
        chat_id=callback_query.from_user.id, 
        message_id=callback_query.message.message_id,
        text=f"Выберите нужный рецепт:",
        reply_markup=keyboard
    )


@recipes_router.callback_query(lambda c: c.data == 'back_to_categories')
async def get_recipe_process_back_to_categories(callback_query: types.CallbackQuery, state: FSMContext):
    await state.set_state(GetRecipeStates.SELECT_CATEGORY)

    keyboard = await get_recipe_get_recipe_categories_keyboard()
    await callback_query.bot.edit_message_text(
        chat_id=callback_query.from_user.id, 
        message_id=callback_query.message.message_id,
        text=f"Выберите {html.bold('категорию')} рецепта",
        reply_markup=keyboard
    )


@recipes_router.callback_query(lambda c: c.data == 'edit_recipe')
async def get_recipe_process_edit_recipe(callback_query: types.CallbackQuery, state: FSMContext):
    await state.set_state(GetRecipeStates.EDIT_RECIPE)

    keyboard = await get_recipe_edit_recipe_keyboard()
    await callback_query.bot.edit_message_text(
        chat_id=callback_query.from_user.id, 
        message_id=callback_query.message.message_id,
        text=f"Выберите {html.bold('поле')}, которое хотите отредактировать",
        reply_markup=keyboard
    )


@recipes_router.callback_query(lambda c: c.data.startswith('field_'), GetRecipeStates.EDIT_RECIPE)
async def get_recipe_process_select_field(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_field = callback_query.data.split('_')[1]
    recipe_id = data['recipe_id']
    recipe = await RecipeRequests.find_one_or_none(id=recipe_id)

    await state.update_data(selected_field=selected_field)
    await state.set_state(GetRecipeStates.SELECT_FIELD)

    message = await callback_query.bot.edit_message_text(
        chat_id=callback_query.from_user.id, 
        message_id=callback_query.message.message_id,
        text=(
            f"Хорошо, вы хотите изменить {html.bold(selected_field)}. "
            f"Введите теперь новое значение.\n\n"
            f"Навсякий случай напомню, что у вас уже написано в этом пункте:\n{getattr(recipe, selected_field)}"
        )
    )
    await state.update_data(message_id_to_edit=message.message_id)


@recipes_router.message(F.text, GetRecipeStates.SELECT_FIELD)
async def get_recipe_process_confirm_edit(message: types.Message, state: FSMContext):
    data = await state.get_data()
    recipe_id = data['recipe_id']
    selected_field = data['selected_field']
    new_value = message.text

    await state.update_data(new_value=new_value, message_id_to_delete=message.message_id)
    recipe = await RecipeRequests.find_one_or_none(id=recipe_id)

    await state.set_state(GetRecipeStates.CONFIRM_EDIT)
    message_id_to_edit = data['message_id_to_edit']

    keyboard = get_recipe_confirm_edit_keyboard()
    await message.bot.edit_message_text(
        chat_id=message.from_user.id, 
        message_id=message_id_to_edit, 
        text=(
            f"Вы уверены, что хотите изменить\n\n"
            f"{html.bold(getattr(recipe, selected_field))}\n\n"
            f"на\n\n{html.bold(new_value)}?"
        ), 
        reply_markup=keyboard
    )


@recipes_router.callback_query(lambda c: c.data == 'confirm_edit', GetRecipeStates.CONFIRM_EDIT)
async def get_recipe_process_confirm_edit(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    recipe_id = data['recipe_id']
    selected_field = data['selected_field']
    new_value = data['new_value']
    message_id_to_delete = data['message_id_to_delete']

    await RecipeRequests.update(id=recipe_id, **{selected_field: new_value})
    await state.set_state(GetRecipeStates.SELECT_RECIPE)

    selected_recipe = await RecipeRequests.find_one_or_none(id=recipe_id)
    recipe_created_by = await UserRequests.find_one_or_none(id=selected_recipe.created_by_id)

    keyboard = get_recipe_cancel_keyboard(is_author=True)
    await callback_query.bot.edit_message_text(
        chat_id=callback_query.from_user.id, 
        message_id=callback_query.message.message_id,
        text=(
            f"Рецепт успешно обновлен!\n\n"
            f"{html.bold(selected_recipe.article)}\n\n"
            f"Ингридиенты:\n{selected_recipe.ingredients}\n\n"
            f"{selected_recipe.steps}\n\n"
            f"Создан пользователем @{recipe_created_by.username}"
        ),
        reply_markup=keyboard
    )
    await callback_query.bot.delete_message(chat_id=callback_query.from_user.id, message_id=message_id_to_delete)


@recipes_router.callback_query(lambda c: c.data in ['back_to_recipe', 'cancel_edit', 'cancel_delete'])
async def get_recipe_process_back_to_recipe(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    recipe_id = data['recipe_id']
    message_id_to_delete = data.get('message_id_to_delete', None)

    await state.set_state(GetRecipeStates.SELECT_RECIPE)

    selected_recipe = await RecipeRequests.find_one_or_none(id=recipe_id)
    recipe_created_by = await UserRequests.find_one_or_none(id=selected_recipe.created_by_id)

    keyboard = get_recipe_cancel_keyboard(is_author=True)
    await callback_query.bot.edit_message_text(
        chat_id=callback_query.from_user.id, 
        message_id=callback_query.message.message_id,
        text=(
            f"{html.bold(selected_recipe.article)}\n\n"
            f"Ингридиенты:\n{selected_recipe.ingredients}\n\n"
            f"{selected_recipe.steps}\n\n"
            f"Создан пользователем @{recipe_created_by.username}"
        ),
        reply_markup=keyboard
    )

    if message_id_to_delete:
        await callback_query.bot.delete_message(chat_id=callback_query.from_user.id, message_id=message_id_to_delete)


@recipes_router.callback_query(lambda c: c.data == 'delete_recipe')
async def get_recipe_process_delete(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    recipe_id = data['recipe_id']

    recipe = await RecipeRequests.find_one_or_none(id=recipe_id)
    await state.set_state(GetRecipeStates.CONFIRM_DELETION)

    keyboard = get_recipe_confirm_deletion_keyboard()
    await callback_query.bot.edit_message_text(
        chat_id=callback_query.from_user.id, 
        message_id=callback_query.message.message_id,
        text=(
            f"Вы уверены, что хотите удалить рецепт {recipe.article}\n\n"
            f"{html.bold('Это действие нельзя отменить!')}"
        ),
        reply_markup=keyboard
    )


@recipes_router.callback_query(lambda c: c.data == 'confirm_delete')
async def get_recipe_process_confirm_delete(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    recipe_id = data['recipe_id']

    await RecipeRequests.delete(id=recipe_id)
    await state.set_state(GetRecipeStates.SELECT_CATEGORY)

    keyboard = await get_recipe_get_recipe_categories_keyboard()
    await callback_query.bot.edit_message_text(
        chat_id=callback_query.from_user.id, 
        message_id=callback_query.message.message_id,
        text=f"{html.bold('Рецепт успешно удален!')}\n\nВыберите {html.bold('категорию')} рецепта", 
        reply_markup=keyboard
    )
