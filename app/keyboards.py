from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.requests import CategoryRequests, RecipeRequests


async def add_recipe_get_recipe_categories_keyboard() -> InlineKeyboardMarkup:
    categories = await CategoryRequests().find_all()
    keyboard = InlineKeyboardBuilder()
    for category in categories:
        keyboard.add(InlineKeyboardButton(text=category.name, callback_data=f"category_{category.id}"))
    return keyboard.adjust(1).as_markup()


def add_recipe_cancel_keyboard()  -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Отменить добавление", callback_data="cancel_adding_recipe")],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return(keyboard)


async def get_recipe_get_recipe_categories_keyboard() -> InlineKeyboardMarkup:
    categories = await CategoryRequests().find_all()
    keyboard = InlineKeyboardBuilder()
    for category in categories:
        recipes = await RecipeRequests().find_all(category_id=category.id)
        if recipes:
            keyboard.add(InlineKeyboardButton(text=category.name, callback_data=f"category_{category.id}"))
    return keyboard.adjust(1).as_markup()

def get_recipe_cancel_keyboard(is_author: bool = False) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Редактировать рецепт", callback_data="edit_recipe")] if is_author else [],
        [InlineKeyboardButton(text="Удалить рецепт", callback_data="delete_recipe")] if is_author else [],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_recipes"), InlineKeyboardButton(text="Отменить", callback_data="cancel_getting_recipe")],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return(keyboard)

async def get_recipe_get_recipes_keyboard(category_id: int) -> InlineKeyboardMarkup:
    recipes = await RecipeRequests().find_all(category_id=category_id)
    keyboard = InlineKeyboardBuilder()

    for recipe in recipes:
        keyboard.add(InlineKeyboardButton(text=recipe.article, callback_data=f"recipe_{recipe.id}"))
    keyboard.adjust(1)

    keyboard.row(
        InlineKeyboardButton(text="Назад", callback_data="back_to_categories"),
        InlineKeyboardButton(text="Отменить", callback_data="cancel_getting_recipe")
    )

    return keyboard.as_markup()


async def get_recipe_edit_recipe_keyboard() -> InlineKeyboardMarkup:
    fields = ['article', 'ingredients', 'steps']
    keyboard = InlineKeyboardBuilder()

    for field in fields:
        keyboard.add(InlineKeyboardButton(text=field, callback_data=f"field_{field}"))
    keyboard.adjust(1)

    keyboard.row(
        InlineKeyboardButton(text="Назад", callback_data="back_to_recipe"),
    )

    return keyboard.as_markup()

def get_recipe_confirm_edit_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Да, изменить", callback_data="confirm_edit")],
        [InlineKeyboardButton(text="Нет, вернуться", callback_data="cancel_edit")],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return(keyboard)

def get_recipe_confirm_deletion_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Да, удалить", callback_data="confirm_delete")],
        [InlineKeyboardButton(text="Нет, вернуться", callback_data="cancel_delete")],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return(keyboard)