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
        [KeyboardButton(text="Информация о продукции")],
        [KeyboardButton(text="Информация о боте")],
        [KeyboardButton(text="Выбрать ручку")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


class ChoosePen(StatesGroup):
    waiting_for_purpose = State()
    waiting_for_ink_color = State()
    waiting_for_line_thickness = State()


class ProductInfo(StatesGroup):
    waiting_for_category = State()
    waiting_for_model = State()


@dp.message(lambda message: message.text == "Поприветствовать")
async def send_welcome(message: types.Message):
    await message.answer("Привет! Я бот-помощник по выбору ручек. Чем могу помочь?", reply_markup=get_keyboard())


@dp.message(lambda message: message.text == "Информация о продукции")
async def start_product_info(message: types.Message, state: FSMContext):
    await state.set_state(ProductInfo.waiting_for_category)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Executive Collection (бизнес-линия)", callback_data="category_business")],
        [InlineKeyboardButton(text="Creative Pro Series (для дизайнеров)", callback_data="category_designer")],
        [InlineKeyboardButton(text="Campus Vibes (студенческая серия)", callback_data="category_economy")]
    ])
    await message.answer("Выберите категорию ручек:", reply_markup=keyboard)


@dp.callback_query(lambda c: c.data.startswith('category_'))
async def process_category(callback_query: types.CallbackQuery, state: FSMContext):
    category_code = callback_query.data.split('_')[1]
    category_names = {
        "business": "Executive Collection (бизнес-линия)",
        "designer": "Creative Pro Series (для дизайнеров)",
        "economy": "Campus Vibes (студенческая серия)"
    }
    category_name = category_names[category_code]
    await state.update_data(category=category_code, category_name=category_name)
    await state.set_state(ProductInfo.waiting_for_model)

    models = {
        "business": ["руководитель", "Professional", "Diplomat"],
        "designer": ["Luxury", "Anniversary", "Special"],
        "economy": ["Student", "Daily", "Basic"]
    }

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=model, callback_data=f"model_{model.lower()}")]
        for model in models[category_code]
    ])

    await callback_query.message.edit_text(f"Вы выбрали категорию: {category_name}\nВыберите модель ручки:",
                                           reply_markup=keyboard)


@dp.callback_query(lambda c: c.data.startswith('model_'))
async def process_model(callback_query: types.CallbackQuery, state: FSMContext):
    model = callback_query.data.split('_')[1]
    data = await state.get_data()
    category = data['category']
    category_name = data['category_name']

    pen_info = {
        ("business",
         "руководитель"): "Модель Executive: элегантная ручка с золотым пером и корпусом из натурального дерева. Идеальна для руководителей и бизнесменов.",
        ("business",
         "professional"): "Модель Professional: надежная ручка с стальным пером и прочным металлическим корпусом. Отлично подходит для длительного использования.",
        ("business",
         "diplomat"): "Модель Diplomat: престижная ручка с платиновым покрытием и гравировкой. Прекрасный выбор для дипломатов и политиков.",
        ("economy",
         "student"): "Модель Student: недорогая, но качественная ручка с эргономичной формой. Идеальна для студентов и школьников.",
        ("economy",
         "daily"): "Модель Daily: практичная ручка для повседневного использования. Имеет удобную grip-зону и долговечные чернила.",
        ("economy",
         "basic"): "Модель Basic: простая и надежная ручка для офисной работы. Экономичный выбор для больших организаций.",
        ("designer",
         "luxury"): "Модель Luxury: эксклюзивная ручка ручной работы с инкрустацией драгоценными камнями. Идеальный подарок для особых случаев.",
        ("designer",
         "anniversary"): "Модель Anniversary: памятная ручка с возможностью персонализации. Отличный выбор для корпоративных юбилеев.",
        ("designer",
         "special"): "Модель Special: уникальная ручка с необычным дизайном. Прекрасный подарок для творческих людей."
    }

    info = pen_info.get((category, model), "Информация о данной модели отсутствует.")

    result_text = f"Категория: {category_name}\nМодель: {model.capitalize()}\n\n{info}"
    await callback_query.message.edit_text(result_text)
    await state.clear()

@dp.message(lambda message: message.text == "Информация о боте")
async def botinfo(message: types.Message):
    await message.answer(
        "Я бот-помощник по выбору ручек. Я могу помочь вам выбрать идеальную ручку или предоставить информацию о нашей продукции.",
        reply_markup=get_keyboard())


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
    await callback_query.message.edit_text(f"Вы выбрали цель: {purpose}\n\nКакой цвет чернил вы предпочитаете?",
                                           reply_markup=keyboard)


@dp.callback_query(lambda c: c.data.startswith('color_'))
async def process_ink_color(callback_query: types.CallbackQuery, state: FSMContext):
    color = callback_query.data.split('_')[1]
    await state.update_data(ink_color=color)
    data = await state.get_data()
    await state.set_state(ChoosePen.waiting_for_line_thickness)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Тонкая", callback_data="thickness_тонкая")],
        [InlineKeyboardButton(text="Средняя", callback_data="thickness_средняя")],
        [InlineKeyboardButton(text="Толстая", callback_data="thickness_толстая")]
    ])
    await callback_query.message.edit_text(
        f"Вы выбрали цель: {data['purpose']}\nЦвет чернил: {color}\n\nКакую толщину линии вы предпочитаете?",
        reply_markup=keyboard)


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

    result_text = f"Ваш выбор:\nЦель: {data['purpose']}\nЦвет чернил: {data['ink_color']}\nТолщина линии: {thickness}\n\n"
    result_text += f"На основе ваших предпочтений, я рекомендую следующую ручку:\n{recommendation}\n\n"
    result_text += "Если вы хотите узнать о других моделях или у вас есть дополнительные вопросы, пожалуйста, дайте мне знать."

    await callback_query.message.edit_text(result_text)
    await state.clear()


@dp.message()
async def echo(message: types.Message):
    await message.answer(
        "Извините, я не понял ваш запрос. Пожалуйста, воспользуйтесь кнопками меню для выбора действия.",
        reply_markup=get_keyboard())


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())