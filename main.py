import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import config
from unsplash.api import Api
from unsplash.auth import Auth

API_TOKEN = config.token

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

auth = Auth('YOUR_ACCESS_KEY', 'YOUR_SECRET_KEY', 'YOUR_REDIRECT_URI')
api = Api(auth)

# Создаем начальную клавиатуру
def get_start_keyboard():
    keyboard = [[KeyboardButton(text="Поприветствовать")]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

# Создаем основную клавиатуру
def get_main_keyboard():
    keyboard = [
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

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Добро пожаловать! Нажмите кнопку 'Поприветствовать', чтобы начать.", reply_markup=get_start_keyboard())

@dp.message(lambda message: message.text == "Поприветствовать")
async def send_welcome(message: types.Message):
    await message.answer("Привет! Я бот-помощник по выбору ручек. Чем могу помочь?", reply_markup=get_main_keyboard())

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
        "business": ["Руководитель", "Профессионал", "Дипломат"],
        "designer": ["Дизайнер", "Писатель", "Художник"],
        "economy": ["Студент", "Начинающий писатель", "Начинающий дизайнер"]
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
        ("business", "руководитель"): "Модель Ювелирная грация: Утонченный корпус украшен замысловатым растительным узором, тщательно вырезанным вручную мастерами своего дела. http://penatelier.tilda.ws/tproduct/475671006932-yuvelirnaya-gratsiya",
        ("business", "профессионал"): "Модель Хрустальная фантазия: Ее уникальный корпус, покрытый мерцающими кристаллами, переливается нежными оттенками розового и лилового, напоминая сказочные сумерки или цветущие поля лаванды. http://penatelier.tilda.ws/tproduct/262098745112-hrustalnaya-fantaziya",
        ("business", "дипломат"): "Модель Изумрудный Элеганс: Элегантный зеленый корпус этой ручки привлекает внимание своей глубиной и насыщенностью. Серебряные детали придают ей утонченный и дорогой вид. http://penatelier.tilda.ws/tproduct/570192768822-izumrudnii-elegans",
        ("economy", "студент"): "Модель Фламинго Блюз: Эта роскошная ручка ручной работы излучает роскошь и яркий стиль. http://penatelier.tilda.ws/tproduct/436039085332-flamingo-blyuz",
        ("economy", "начинающий писатель"): "Модель Гармония Огонь и Лед: Ярко-оранжевый корпус в сочетании с глубоким синим оттенком делает ее заметной и стильной. Металлические детали придают ей элегантность и прочность. http://penatelier.tilda.ws/tproduct/467939644822-garmoniya-ogon-i-led",
        ("economy", "начинающий дизайнер"): "Модель Basic: простая и надежная ручка для офисной работы. Экономичный выбор для больших организаций.",
        ("designer", "дизайнер"): "Модель Калейдоскоп красок: Корпус покрыт ярким калейдоскопом цветов и форм, создающих неповторимый узор, полный жизни и энергии. http://penatelier.tilda.ws/tproduct/696281938322-kaleidoskop-krasok",
        ("designer", "писатель"): "Модель Вихрь Вдохновения:  Многоцветные спирали на корпусе напоминают о бесконечности креативных идей. Золотые акценты добавляют нотку роскоши и утонченности. http://penatelier.tilda.ws/tproduct/509816028762-vihr-vdohnoveniya",
        ("designer", "художник"): "Модель Special: уникальная ручка с необычным дизайном. Прекрасный подарок для творческих людей."
    }

    info = pen_info.get((category, model), "Информация о данной модели отсутствует.")

    result_text = f"Категория: {category_name}\nМодель: {model.capitalize()}\n\n{info}"
    await callback_query.message.edit_text(result_text)
    await state.clear()

@dp.message(lambda message: message.text == "Информация о боте")
async def botinfo(message: types.Message):
    await message.answer(
        "Я бот-помощник по выбору ручек. Я могу помочь вам выбрать идеальную ручку или предоставить информацию о нашей продукции.",
        reply_markup=get_main_keyboard())

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
        reply_markup=get_main_keyboard())

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())