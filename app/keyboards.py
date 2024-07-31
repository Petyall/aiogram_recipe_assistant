from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.requests import CategoryRequests, RecipeRequests


async def add_recipe_get_recipe_categories_keyboard():
    categories = await CategoryRequests().find_all()
    keyboard = InlineKeyboardBuilder()
    for category in categories:
        keyboard.add(InlineKeyboardButton(text=category.name, callback_data=f"category_{category.id}"))
    return keyboard.adjust(1).as_markup()


def add_recipe_cancel_keyboard():
    buttons = [
        [InlineKeyboardButton(text="Отменить добавление", callback_data="cancel_adding_recipe")],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return(keyboard)


async def get_recipe_get_recipe_categories_keyboard():
    categories = await CategoryRequests().find_all()
    keyboard = InlineKeyboardBuilder()
    for category in categories:
        recipes = await RecipeRequests().find_all(category_id=category.id)
        if recipes:
            keyboard.add(InlineKeyboardButton(text=category.name, callback_data=f"category_{category.id}"))
    return keyboard.adjust(1).as_markup()

def get_recipe_cancel_keyboard():
    buttons = [
        [InlineKeyboardButton(text="Отменить", callback_data="cancel_getting_recipe"), InlineKeyboardButton(text="Назад", callback_data="back_to_recipes")],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return(keyboard)

async def get_recipe_get_recipes_keyboard(category_id: int):
    recipes = await RecipeRequests().find_all(category_id=category_id)
    keyboard = InlineKeyboardBuilder()
    for recipe in recipes:
        keyboard.add(InlineKeyboardButton(text=recipe.article, callback_data=f"recipe_{recipe.id}"))
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data="back_to_categories"))
    keyboard.add(InlineKeyboardButton(text="Отменить", callback_data="cancel_getting_recipe"))
    return keyboard.adjust(1).as_markup()