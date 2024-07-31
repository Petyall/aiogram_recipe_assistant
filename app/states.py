from aiogram.fsm.state import State, StatesGroup


class AddRecipeStates(StatesGroup):
    SELECT_CATEGORY = State()
    GET_ARTICLE = State()
    GET_INGREDIENTS = State()
    GET_STEPS = State()


class GetRecipeStates(StatesGroup):
    SELECT_CATEGORY = State()
    SELECT_RECIPE = State()