from aiogram import F, Router, html, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app.config import settings
from app.keyboards import (add_recipe_get_recipe_categories_keyboard,
                           cancel_adding_keyboard, get_recipe_cancel_keyboard,
                           get_recipe_confirm_keyboard,
                           get_recipe_edit_recipe_keyboard,
                           get_recipe_get_recipe_categories_keyboard,
                           get_recipe_get_recipes_keyboard)
from app.requests import CategoryRequests, RecipeRequests, UserRequests
from app.states import (AddCategoryStates, AddRecipeStates, AddUserStates,
                        GetRecipeStates)

recipes_router = Router()


# Обработчик команды добавления рецепта
@recipes_router.message(Command("add_recipe"))
async def cmd_add_recipe(message: types.Message, state: FSMContext):
    # Установка состояния FSM
    await state.set_state(AddRecipeStates.SELECT_CATEGORY)
    # Получение клавиатуры
    keyboard = await add_recipe_get_recipe_categories_keyboard()
    # Отправка сообщения
    await message.reply(
        text=f"Выберите {html.bold('категорию')} нового рецепта", reply_markup=keyboard
    )


# Обработчик выбора категории для добавления рецепта
@recipes_router.callback_query(lambda c: c.data.startswith("category_"), AddRecipeStates.SELECT_CATEGORY)
async def add_recipe_process_select_category(callback_query: types.CallbackQuery, state: FSMContext):
    # Получение выбранной категории (из инлайн клавиатуры)
    category_id = int(callback_query.data.split("_")[1])
    selected_category = await CategoryRequests.find_one_or_none(id=category_id)
    # Обновление данных FSM
    await state.update_data(recipe_category=selected_category.id)
    # Установка состояния FSM 
    await state.set_state(AddRecipeStates.GET_ARTICLE)

    # Получение клавиатуры
    keyboard = cancel_adding_keyboard(type="recipe")
    # Отправка сообщения
    message = await callback_query.bot.edit_message_text(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        text=(
            f"Понял, Вы хотите добавить {selected_category.name.lower()}. "
            f"Введите {html.bold('название')} рецепта:"
        ),
        reply_markup=keyboard,
    )
    # Сохранение ID сообщения (нужно для удаления клавиатуры, если пользователь ввел название рецепта
    # и перешел на следующее состояние)
    await state.update_data(message_id=message.message_id)


# Обработчик ввода названия рецепта
@recipes_router.message(F.text, AddRecipeStates.GET_ARTICLE)
async def add_recipe_process_get_article(message: types.Message, state: FSMContext):
    # Получение названия рецепта из сообщения
    recipe_article = message.text
    # Обновление данных FSM
    await state.update_data(recipe_article=recipe_article)
    # Установка состояния FSM
    await state.set_state(AddRecipeStates.GET_INGREDIENTS)

    # Удаление клавиатуры с кнопкой отмены в прошлом сообщении (если такое существует)
    data = await state.get_data()
    if "message_id" in data:
        await message.bot.edit_message_reply_markup(
            chat_id=message.from_user.id,
            message_id=data["message_id"],
            reply_markup=None,
        )

    # Получение клавиатуры
    keyboard = cancel_adding_keyboard(type="recipe")
    # Отправка сообщения
    new_message = await message.reply(
        text=f"Отлично! Теперь введите {html.bold('ингридиенты')} рецепта:",
        reply_markup=keyboard,
    )
    # Сохранение ID сообщения
    await state.update_data(message_id=new_message.message_id)


# Обработчик ввода ингридиентов
@recipes_router.message(F.text, AddRecipeStates.GET_INGREDIENTS)
async def add_recipe_process_get_ingredients(message: types.Message, state: FSMContext):
    # Получение ингридиентов из сообщения
    recipe_ingredients = message.text
    # Обновление данных FSM
    await state.update_data(recipe_ingredients=recipe_ingredients)
    # Установка состояния FSM
    await state.set_state(AddRecipeStates.GET_STEPS)

    # Удаление клавиатуры с кнопкой отмены в прошлом сообщении (если такое существует)
    data = await state.get_data()
    if "message_id" in data:
        await message.bot.edit_message_reply_markup(
            chat_id=message.from_user.id,
            message_id=data["message_id"],
            reply_markup=None,
        )

    # Получение клавиатуры
    keyboard = cancel_adding_keyboard(type="recipe")
    # Отправка сообщения
    new_message = await message.reply(
        text=f"Остался последний пункт! Введите {html.bold('шаги')} рецепта:",
        reply_markup=keyboard,
    )
    # Сохранение ID сообщения
    await state.update_data(message_id=new_message.message_id)


# Обработчик ввода шагов
@recipes_router.message(F.text, AddRecipeStates.GET_STEPS)
async def add_recipe_process_get_steps(message: types.Message, state: FSMContext):
    # Получение всех введенных данных
    data = await state.get_data()
    recipe_article = data["recipe_article"]
    recipe_ingredients = data["recipe_ingredients"]
    recipe_category = data["recipe_category"]
    recipe_steps = message.text

    # Получение пользователя из БД, добавляющего рецепт
    username = message.from_user.username
    user = await UserRequests.find_one_or_none(username=username)
    # Костыль для получения telegram ID пользователя (нужен для мидлвейр с вайт-листом)
    if user:
        await UserRequests.update(username=username, id=message.from_user.id)
    recipe_created_by = user.id

    # Добавление рецепта в БД
    await RecipeRequests.add(
        article=recipe_article,
        ingredients=recipe_ingredients,
        steps=recipe_steps,
        category_id=recipe_category,
        created_by_id=recipe_created_by,
    )

    # Очистка FSM
    await state.clear()
    # Отправка сообщения
    await message.reply(text=f"Супер! Теперь я знаю рецепт {html.bold(recipe_article)}")
    await message.answer_sticker(
        sticker="CAACAgIAAxkBAAEHalZmreLHu9xcSQsIvVNst2SDKXKrBwAC6jYAAlzHwEojRC8Od4h7-DUE"
    )


# Обработчик нажатия кнопки отмены
@recipes_router.callback_query(lambda c: c.data == "cancel_adding_recipe")
async def add_recipe_process_cancel(callback_query: types.CallbackQuery, state: FSMContext):
    # Очистка FSM
    await state.clear()
    # Отправка сообщения
    await callback_query.bot.edit_message_text(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        text="Добавление рецепта завершено",
    )


# Обработчик команды получения рецепта
@recipes_router.message(Command("get_recipe"))
async def cmd_get_recipe(message: types.Message, state: FSMContext):
    # Установка состояния FSM
    await state.set_state(GetRecipeStates.SELECT_CATEGORY)
    # Получение клавиатуры
    keyboard = await get_recipe_get_recipe_categories_keyboard()
    # Отправка сообщения
    await message.reply(
        f"Выберите {html.bold('категорию')} рецепта", reply_markup=keyboard
    )


@recipes_router.callback_query(lambda c: c.data.startswith("category_"), GetRecipeStates.SELECT_CATEGORY)
async def get_recipe_process_select_category(callback_query: types.CallbackQuery, state: FSMContext):
    # Получение выбранной категории (из инлайн клавиатуры)
    category_id = int(callback_query.data.split("_")[1])
    selected_category = await CategoryRequests.find_one_or_none(id=category_id)

    # Обновление данных FSM
    await state.update_data(recipe_category=selected_category.id)
    await state.set_state(GetRecipeStates.SELECT_RECIPE)

    # Получение клавиатуры
    keyboard = await get_recipe_get_recipes_keyboard(category_id)
    # Отправка сообщения
    await callback_query.bot.edit_message_text(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        text=f"Выберите нужный рецепт:",
        reply_markup=keyboard,
    )


# Обработчик выбора рецепта
@recipes_router.callback_query(lambda c: c.data.startswith("recipe_"), GetRecipeStates.SELECT_RECIPE)
async def get_recipe_process_select_recipe(callback_query: types.CallbackQuery, state: FSMContext):
    # Получение выбранного рецепта (из инлайн клавиатуры)
    recipe_id = int(callback_query.data.split("_")[1])
    # Обновление данных FSM
    await state.update_data(recipe_id=recipe_id)
    # Получение рецепта
    selected_recipe = await RecipeRequests.find_one_or_none(id=recipe_id)
    # Получение пользователя, создавшего рецепт
    recipe_created_by = await UserRequests.find_one_or_none(
        id=selected_recipe.created_by_id
    )

    # Проверка автора рецепта (для добавления кнопок удаления и редактирования)
    is_author = selected_recipe.created_by_id == callback_query.from_user.id
    # Получение клавиатуры
    keyboard = get_recipe_cancel_keyboard(is_author)
    # Отправка сообщения
    await callback_query.bot.edit_message_text(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        text=(
            f"{html.bold(selected_recipe.article)}\n\n"
            f"Ингридиенты:\n{selected_recipe.ingredients}\n\n"
            f"{selected_recipe.steps}\n\n"
            f"Создан пользователем @{recipe_created_by.username}"
        ),
        reply_markup=keyboard,
    )


# Обработчик отмены получения рецепта
@recipes_router.callback_query(lambda c: c.data == "cancel_getting_recipe")
async def get_recipe_process_cancel(callback_query: types.CallbackQuery, state: FSMContext):
    # Очистка FSM
    await state.clear()
    # Отправка сообщения
    await callback_query.bot.edit_message_text(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        text="Просмотр рецепта завершен",
    )


# Обработчик нажатия кнопки "Назад" (к рецептам)
@recipes_router.callback_query(lambda c: c.data == "back_to_recipes")
async def get_recipe_process_back_to_recipes(callback_query: types.CallbackQuery, state: FSMContext):
    # Получение id категории из FSM
    data = await state.get_data()
    category_id = data["recipe_category"]

    # Установка состояния FSM
    await state.set_state(GetRecipeStates.SELECT_RECIPE)

    # Получение клавиатуры
    keyboard = await get_recipe_get_recipes_keyboard(category_id)
    # Отправка сообщения
    await callback_query.bot.edit_message_text(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        text=f"Выберите нужный рецепт:",
        reply_markup=keyboard,
    )


# Обработчик нажатия кнопки "Назад" (к категориям)
@recipes_router.callback_query(lambda c: c.data == "back_to_categories")
async def get_recipe_process_back_to_categories(callback_query: types.CallbackQuery, state: FSMContext):
    # Установка состояния FSM
    await state.set_state(GetRecipeStates.SELECT_CATEGORY)

    # Получение клавиатуры
    keyboard = await get_recipe_get_recipe_categories_keyboard()
    # Отправка сообщения
    await callback_query.bot.edit_message_text(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        text=f"Выберите {html.bold('категорию')} рецепта",
        reply_markup=keyboard,
    )


# Обработчик нажатия кнопки "Редактировать"
@recipes_router.callback_query(lambda c: c.data == "edit_recipe")
async def get_recipe_process_edit_recipe(callback_query: types.CallbackQuery, state: FSMContext):
    # Установка состояния FSM
    await state.set_state(GetRecipeStates.EDIT_RECIPE)

    # Получение клавиатуры
    keyboard = await get_recipe_edit_recipe_keyboard()
    # Отправка сообщения
    await callback_query.bot.edit_message_text(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        text=f"Выберите {html.bold('поле')}, которое хотите отредактировать",
        reply_markup=keyboard,
    )


# Обработчик выбора поля редактирования
@recipes_router.callback_query(lambda c: c.data.startswith("field_"), GetRecipeStates.EDIT_RECIPE)
async def get_recipe_process_select_field(callback_query: types.CallbackQuery, state: FSMContext):
    # Получение id рецепта из FSM
    data = await state.get_data()
    recipe_id = data["recipe_id"]
    recipe = await RecipeRequests.find_one_or_none(id=recipe_id)

    # Получение выбранного поля редактирования
    selected_field = callback_query.data.split("_")[1]

    # Обновление данных FSM
    await state.update_data(selected_field=selected_field)
    # Установка состояния FSM
    await state.set_state(GetRecipeStates.SELECT_FIELD)

    # Отправка сообщения
    message = await callback_query.bot.edit_message_text(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        text=(
            f"Хорошо, вы хотите изменить {html.bold(selected_field)}. "
            f"Введите теперь новое значение.\n\n"
            f"Навсякий случай напомню, что у вас уже написано в этом пункте:\n{getattr(recipe, selected_field)}"
        ),
    )
    # Сохранение id сообщения для редактирования
    await state.update_data(message_id_to_edit=message.message_id)


# Обработчик подтверждения редактирования
@recipes_router.message(F.text, GetRecipeStates.SELECT_FIELD)
async def get_recipe_process_confirm_edit(message: types.Message, state: FSMContext):
    # Получение данных из FSM
    data = await state.get_data()
    recipe_id = data["recipe_id"]
    selected_field = data["selected_field"]
    new_value = message.text

    # Обновление данных FSM
    await state.update_data(
        new_value=new_value, message_id_to_delete=message.message_id
    )

    # Получение рецепта
    recipe = await RecipeRequests.find_one_or_none(id=recipe_id)

    # Установка состояния FSM
    await state.set_state(GetRecipeStates.CONFIRM_EDIT)

    # Получение ID сообщения для редактирования
    message_id_to_edit = data["message_id_to_edit"]
    # Получение клавиатуры
    keyboard = get_recipe_confirm_keyboard(type="edit")
    # Отправка сообщения
    await message.bot.edit_message_text(
        chat_id=message.from_user.id,
        message_id=message_id_to_edit,
        text=(
            f"Вы уверены, что хотите изменить\n\n"
            f"{html.bold(getattr(recipe, selected_field))}\n\n"
            f"на\n\n{html.bold(new_value)}?"
        ),
        reply_markup=keyboard,
    )


# Обработчик подтверждения редактирования   
@recipes_router.callback_query(lambda c: c.data == "confirm_edit", GetRecipeStates.CONFIRM_EDIT)
async def get_recipe_process_confirm_edit(callback_query: types.CallbackQuery, state: FSMContext):
    # Получение данных из FSM
    data = await state.get_data()
    recipe_id = data["recipe_id"]
    selected_field = data["selected_field"]
    new_value = data["new_value"]
    message_id_to_delete = data["message_id_to_delete"]

    # Обновление рецепта
    await RecipeRequests.update(id=recipe_id, **{selected_field: new_value})
    # Установка состояния FSM
    await state.set_state(GetRecipeStates.SELECT_RECIPE)

    # Получение обновленного рецепта
    selected_recipe = await RecipeRequests.find_one_or_none(id=recipe_id)
    recipe_created_by = await UserRequests.find_one_or_none(
        id=selected_recipe.created_by_id
    )

    # Получение клавиатуры
    keyboard = get_recipe_cancel_keyboard(is_author=True)
    # Отправка сообщения
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
        reply_markup=keyboard,
    )
    # Удаление сообщения пользователя
    await callback_query.bot.delete_message(
        chat_id=callback_query.from_user.id, message_id=message_id_to_delete
    )


# Обработчик возврата к рецептам
@recipes_router.callback_query(lambda c: c.data in ["back_to_recipe", "cancel_edit", "cancel_delete"])
async def get_recipe_process_back_to_recipe(callback_query: types.CallbackQuery, state: FSMContext):
    # Получение данных FSM
    data = await state.get_data()
    recipe_id = data["recipe_id"]
    message_id_to_delete = data.get("message_id_to_delete", None)

    # Установка состояния FSM
    await state.set_state(GetRecipeStates.SELECT_RECIPE)

    # Получение рецепта
    selected_recipe = await RecipeRequests.find_one_or_none(id=recipe_id)
    recipe_created_by = await UserRequests.find_one_or_none(
        id=selected_recipe.created_by_id
    )

    # Получение клавиатуры
    keyboard = get_recipe_cancel_keyboard(is_author=True)
    # Отправка сообщения
    await callback_query.bot.edit_message_text(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        text=(
            f"{html.bold(selected_recipe.article)}\n\n"
            f"Ингридиенты:\n{selected_recipe.ingredients}\n\n"
            f"{selected_recipe.steps}\n\n"
            f"Создан пользователем @{recipe_created_by.username}"
        ),
        reply_markup=keyboard,
    )

    # Удаление сообщения пользователя (если есть)
    if message_id_to_delete:
        await callback_query.bot.delete_message(
            chat_id=callback_query.from_user.id, message_id=message_id_to_delete
        )


# Обработчик удаления рецепта
@recipes_router.callback_query(lambda c: c.data == "delete_recipe")
async def get_recipe_process_delete(callback_query: types.CallbackQuery, state: FSMContext):
    # Получение id рецепта из FSM
    data = await state.get_data()
    recipe_id = data["recipe_id"]

    # Получение рецепта
    recipe = await RecipeRequests.find_one_or_none(id=recipe_id)
    # Установка состояния FSM
    await state.set_state(GetRecipeStates.CONFIRM_DELETION)

    # Получение клавиатуры
    keyboard = get_recipe_confirm_keyboard(type="delete")
    # Отправка сообщения
    await callback_query.bot.edit_message_text(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        text=(
            f"Вы уверены, что хотите удалить рецепт {recipe.article}\n\n"
            f"{html.bold('Это действие нельзя отменить!')}"
        ),
        reply_markup=keyboard,
    )


# Обработчик подтверждения удаления 
@recipes_router.callback_query(lambda c: c.data == "confirm_delete")
async def get_recipe_process_confirm_delete(callback_query: types.CallbackQuery, state: FSMContext):
    # Получение id рецепта из FSM
    data = await state.get_data()
    recipe_id = data["recipe_id"]

    # Удаление рецепта
    await RecipeRequests.delete(id=recipe_id)
    # Установка состояния FSM
    await state.set_state(GetRecipeStates.SELECT_CATEGORY)

    # Получение клавиатуры
    keyboard = await get_recipe_get_recipe_categories_keyboard()
    # Отправка сообщения
    await callback_query.bot.edit_message_text(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        text=f"{html.bold('Рецепт успешно удален!')}\n\nВыберите {html.bold('категорию')} рецепта",
        reply_markup=keyboard,
    )


# Обработчик команды добавления пользователя
@recipes_router.message(Command("add_user"))
async def cmd_add_user(message: types.Message, state: FSMContext):
    # Проверка на права админа
    if message.from_user.id != settings.ADMIN_ID:
        return

    # Установка состояния FSM
    await state.set_state(AddUserStates.GET_USERNAME)
    # Отправка сообщения
    await message.answer(
        text="Отправь username пользователя",
        reply_markup=cancel_adding_keyboard(type="user"),
    )


# Обработчик добавления пользователя
@recipes_router.message(AddUserStates.GET_USERNAME)
async def add_user(message: types.Message, state: FSMContext):
    # Получение username
    username = message.text
    # Добавление пользователя в БД
    await UserRequests.add(username=username)
    # Очистка FSM
    await state.clear()
    # Отправка сообщения
    await message.answer(text=f"Пользователь {username} успешно добавлен!")


# Обработчик команды добавления категории
@recipes_router.message(Command("add_category"))
async def cmd_add_category(message: types.Message, state: FSMContext):
    # Проверка на права админа
    if message.from_user.id != settings.ADMIN_ID:
        return

    # Установка состояния FSM
    await state.set_state(AddCategoryStates.GET_ROLE_NAME)
    # Отправка сообщения
    await message.answer(
        text="Отправь название категории",
        reply_markup=cancel_adding_keyboard(type="category"),
    )


# Обработчик добавления категории
@recipes_router.message(AddCategoryStates.GET_ROLE_NAME)
async def add_category(message: types.Message, state: FSMContext):
    # Получение названия категории
    name = message.text
    # Добавление категории в БД
    await CategoryRequests.add(name=name)
    # Очистка FSM
    await state.clear()
    # Отправка сообщения
    await message.answer(text=f"Категория {name} успешно добавлена!")


# Обработчик отмены добавления
@recipes_router.callback_query(lambda c: c.data in ["cancel_adding_category", "cancel_adding_user"])
async def add_category_process_cancel_adding_user_or_category(callback_query: types.CallbackQuery, state: FSMContext):
    # Очистка FSM
    await state.clear()
    # Удаление сообщения
    await callback_query.bot.delete_message(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
    )
