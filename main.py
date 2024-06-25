import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import config

API_TOKEN = config.token

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# Создаем клавиатуру
def get_keyboard():
    keyboard = [
        [KeyboardButton(text="Поприветствовать")],
        [KeyboardButton(text="Крикнуть 'Ура!'")],
        [KeyboardButton(text="Информация о боте")],
        [KeyboardButton(text="Выбрать ручку")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


class ChoosePen(StatesGroup):
    waiting_for_purpose = State()
    waiting_for_ink_color = State()
    waiting_for_line_thickness = State()


@dp.message(lambda message: message.text == "Поприветствовать")
async def send_welcome(message: types.Message):
    await message.answer("Привет! Я эхобот на aiogram 3. Отправь мне любое сообщение, и я повторю его.",
                         reply_markup=get_keyboard())


@dp.message(lambda message: message.text == "Крикнуть 'Ура!'")
async def send_ura(message: types.Message):
    await message.answer("УРАААА! Я эхобот на aiogram 3. Отправь мне любое сообщение, и я повторю его.",
                         reply_markup=get_keyboard())


@dp.message(lambda message: message.text == "Информация о боте")
async def botinfo(message: types.Message):
    await message.answer("Информация по этому боту не заполнена", reply_markup=get_keyboard())


@dp.message(lambda message: message.text == "Выбрать ручку")
async def start_choose_pen(message: types.Message, state: FSMContext):
    await state.set_state(ChoosePen.waiting_for_purpose)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Работа", callback_data="purpose_работа")],
        [InlineKeyboardButton(text="Учеба", callback_data="purpose_учеба")],
        [InlineKeyboardButton(text="Творчество", callback_data="purpose_творчество")]
    ])
    await message.answer("Для каких целей вам нужна ручка?", reply_markup=keyboard)


@dp.callback_query(lambda c: c.data.startswith('purpose_'))
async def process_purpose(callback_query: types.CallbackQuery, state: FSMContext):
    purpose = callback_query.data.split('_')[1]
    await state.update_data(purpose=purpose)
    await state.set_state(ChoosePen.waiting_for_ink_color)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Синий", callback_data="color_синий")],
        [InlineKeyboardButton(text="Черный", callback_data="color_черный")],
        [InlineKeyboardButton(text="Красный", callback_data="color_красный")]
    ])
    await callback_query.message.edit_text("Какой цвет чернил вы предпочитаете?", reply_markup=keyboard)


@dp.callback_query(lambda c: c.data.startswith('color_'))
async def process_ink_color(callback_query: types.CallbackQuery, state: FSMContext):
    color = callback_query.data.split('_')[1]
    await state.update_data(ink_color=color)
    await state.set_state(ChoosePen.waiting_for_line_thickness)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Тонкая", callback_data="thickness_тонкая")],
        [InlineKeyboardButton(text="Средняя", callback_data="thickness_средняя")],
        [InlineKeyboardButton(text="Толстая", callback_data="thickness_толстая")]
    ])
    await callback_query.message.edit_text("Какую толщину линии вы предпочитаете?", reply_markup=keyboard)


@dp.callback_query(lambda c: c.data.startswith('thickness_'))
async def process_line_thickness(callback_query: types.CallbackQuery, state: FSMContext):
    thickness = callback_query.data.split('_')[1]
    await state.update_data(line_thickness=thickness)

    data = await state.get_data()

    pen_recommendations = {
        ("работа", "синий", "средняя"): "Модель 'ОфисПро': идеальна для ежедневной работы с документами",
        ("учеба", "черный", "тонкая"): "Модель 'СтудиУм': отлично подходит для конспектов и заметок",
        ("творчество", "красный", "толстая"): "Модель 'АртЛайн': прекрасный выбор для творческих проектов",
    }

    recommendation = pen_recommendations.get(
        (data['purpose'], data['ink_color'], data['line_thickness']),
        "Стандартная модель 'Универсал': подходит для различных задач"
    )

    await callback_query.message.edit_text(
        f"На основе ваших предпочтений, я рекомендую следующую ручку:\n{recommendation}\n\nЕсли вы хотите узнать о других моделях или у вас есть дополнительные вопросы, пожалуйста, дайте мне знать.")
    await state.clear()


@dp.message()
async def echo(message: types.Message):
    await message.answer(message.text, reply_markup=get_keyboard())


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())