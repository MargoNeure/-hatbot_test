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
import aiohttp

UNSPLASH_ACCESS_KEY = 'yClbk2wsSbgx0ein8r5R6Sep7gitarrvGus5Rq9QkIA'  # Замените на ваш ключ доступа Unsplash
UNSPLASH_SECRET_KEY = 'itAcdoXaOd20u6JDRgyfY8N1k8sef9ALL4IgJSJrnYI'  # Замените на ваш секретный ключ Unsplash
UNSPLASH_REDIRECT_URI = '622581'  # Замените на ваш URI перенаправления

API_TOKEN = config.token

logging.basicConfig(level=logging.INFO)



logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Настройка Unsplash API
auth = Auth(UNSPLASH_ACCESS_KEY, UNSPLASH_SECRET_KEY, UNSPLASH_REDIRECT_URI)
api = Api(auth)

# Создаем клавиатуры
def get_start_keyboard():
    keyboard = [[KeyboardButton(text="Поприветствовать")]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_main_keyboard():
    keyboard = [
        [KeyboardButton(text="Информация о продукции")],
        [KeyboardButton(text="Информация о боте")],
        [KeyboardButton(text="Выбрать ручку")],
        [KeyboardButton(text="Показать картинку ручки")]  # Новая кнопка
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

async def get_image_from_unsplash(query):
    try:
        photos = api.search.photos(query, per_page=1)
        if photos and photos['results']:
            return photos['results'][0].urls.small
        else:
            return None
    except Exception as e:
        print(f"Ошибка при запросе к Unsplash API: {e}")
        return None

@dp.callback_query(lambda c: c.data.startswith('model_'))
async def process_model(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    model = callback_query.data.split('_')[1]
    data = await state.get_data()
    category = data['category']
    category_name = data['category_name']

    await callback_query.message.edit_text("Загрузка информации...")

    # Здесь должен быть ваш код для получения информации о ручке
    # Пример:
    pen_info = f"Информация о модели {model.capitalize()} из категории {category_name}"

    # Получаем изображение из Unsplash
    image_url = await get_image_from_unsplash(f"{category} pen {model}")

    result_text = f"Категория: {category_name}\nМодель: {model.capitalize()}\n\n{pen_info}"

    if image_url:
        # Отправляем изображение с подписью
        await callback_query.message.answer_photo(photo=image_url, caption=result_text)
    else:
        # Если изображение не найдено, отправляем только текст
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

    # Получаем изображение из Unsplash для рекомендованной ручки
    image_url = await get_image_from_unsplash(f"{data['purpose']} pen {data['ink_color']} {thickness}")

    if image_url:
        await callback_query.message.answer_photo(photo=image_url, caption=result_text)
    else:
        await callback_query.message.edit_text(result_text)

    await state.clear()

    @dp.message(lambda message: message.text == "Показать картинку ручки")
    async def show_pen_image(message: types.Message):
        await message.answer("Пожалуйста, выберите тип ручки:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Бизнес-ручка", callback_data="image_business")],
            [InlineKeyboardButton(text="Дизайнерская ручка", callback_data="image_designer")],
            [InlineKeyboardButton(text="Студенческая ручка", callback_data="image_student")]
        ]))

    @dp.callback_query(lambda c: c.data.startswith('image_'))
    async def process_image_choice(callback_query: types.CallbackQuery):
        pen_type = callback_query.data.split('_')[1]
        image_query = f"{pen_type} pen"

        await callback_query.answer()
        await callback_query.message.edit_text("Загрузка изображения...")

        image_url = await get_image_from_unsplash(image_query)

        if image_url:
            await callback_query.message.answer_photo(photo=image_url, caption=f"Вот изображение {pen_type} ручки")
        else:
            await callback_query.message.edit_text("К сожалению, не удалось найти подходящее изображение.")

async def get_image_from_unsplash(query):
    try:
        photos = api.search.photos(query, per_page=1)
        if photos and photos['results']:
            return photos['results'][0].urls.small
        else:
            return None
    except Exception as e:
        print(f"Ошибка при запросе к Unsplash API: {e}")
        return None

@dp.message()
async def echo(message: types.Message):
    await message.answer(
        "Извините, я не понял ваш запрос. Пожалуйста, воспользуйтесь кнопками меню для выбора действия.",
        reply_markup=get_main_keyboard())

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())