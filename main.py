import logging
import asyncio
import random
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

API_TOKEN = config.token
UNSPLASH_ACCESS_KEY = config.key1
UNSPLASH_SECRET_KEY = config.key2
UNSPLASH_REDIRECT_URI = config.key3

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
        [KeyboardButton(text="Картинки Unsplash")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


class ChoosePen(StatesGroup):
    waiting_for_purpose = State()
    waiting_for_ink_color = State()
    waiting_for_line_thickness = State()


class ProductInfo(StatesGroup):
    waiting_for_category = State()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Добро пожаловать! Нажмите кнопку 'Поприветствовать', чтобы начать.",
                         reply_markup=get_start_keyboard())


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
    category_info = {
        "business": "Executive Collection (бизнес-линия): Элегантные ручки премиум-класса для деловых встреч и важных подписаний. https://tilda.ru/page/preview/?pageid=50333639&lang=RU#rec759761127",
        "designer": "Creative Pro Series (для дизайнеров): Ручки с широким спектром цветов и толщин линий для творческих задач. https://tilda.ru/page/preview/?pageid=50333639&lang=RU#rec759763977",
        "economy": "Campus Vibes (студенческая серия): Надежные и доступные ручки для ежедневного использования в учебе. https://tilda.ru/page/preview/?pageid=50333639&lang=RU#rec759765315"
    }

    info = category_info.get(category_code, "Информация о данной категории отсутствует.")

    await callback_query.message.edit_text(f"Информация о категории:\n\n{info}")
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
        ("работа", "синий",
         "средняя"): "Модель 'Ювелирная грация': идеальна для ежедневной работы с документами http://penatelier.tilda.ws/tproduct/475671006932-yuvelirnaya-gratsiya",
        ("учеба", "черный",
         "тонкая"): "Модель 'Гармония Огонь и Лед': отлично подходит для конспектов и заметок  http://penatelier.tilda.ws/tproduct/467939644822-garmoniya-ogon-i-led",
        ("творчество", "красный",
         "толстая"): "Модель 'Вихрь Вдохновения': прекрасный выбор для творческих проектов http://penatelier.tilda.ws/tproduct/509816028762-vihr-vdohnoveniya",
    }

    recommendation = pen_recommendations.get(
        (data['purpose'], data['ink_color'], data['line_thickness']),
        "Стандартная модель 'Фламинго Блюз': подходит для различных задач http://penatelier.tilda.ws/tproduct/436039085332-flamingo-blyuz"
    )

    result_text = f"Ваш выбор:\nЦель: {data['purpose']}\nЦвет чернил: {data['ink_color']}\nТолщина линии: {thickness}\n\n"
    result_text += f"На основе ваших предпочтений, я рекомендую следующую ручку:\n{recommendation}\n\n"
    result_text += "Если вы хотите узнать о других моделях или у вас есть дополнительные вопросы, пожалуйста, дайте мне знать."

    await callback_query.message.edit_text(result_text)
    await state.clear()


async def get_image_from_unsplash(query):
    try:
        # Попробуем сначала на английском языке
        photos = api.search.photos(query, per_page=30)
        if photos and photos['results']:
            return random.choice(photos['results']).urls.small

        # Если не нашли, попробуем на русском
        ru_query = {
            "pen": "ручка",
            "pencil": "карандаш",
            "contract": "договор",
            "drawing": "рисунок",
            "book": "книга"
        }.get(query, query)

        photos = api.search.photos(ru_query, per_page=30)
        if photos and photos['results']:
            return random.choice(photos['results']).urls.small

        return None
    except Exception as e:
        print(f"Ошибка при запросе к Unsplash API: {e}")
        return None


@dp.message(lambda message: message.text == "Картинки Unsplash")
async def show_unsplash_options(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ручка", callback_data="unsplash_pen")],
        [InlineKeyboardButton(text="Карандаш", callback_data="unsplash_pencil")],
        [InlineKeyboardButton(text="Договор", callback_data="unsplash_contract")],
        [InlineKeyboardButton(text="Рисунок", callback_data="unsplash_drawing")],
        [InlineKeyboardButton(text="Книга", callback_data="unsplash_book")]
    ])
    await message.answer("Выберите категорию для поиска изображения:", reply_markup=keyboard)


@dp.callback_query(lambda c: c.data.startswith('unsplash_'))
async def process_unsplash_choice(callback_query: types.CallbackQuery):
    category = callback_query.data.split('_')[1]
    categories = {
        "pen": "ручка",
        "pencil": "карандаш",
        "contract": "договор",
        "drawing": "рисунок",
        "book": "книга"
    }

    await callback_query.answer()
    await callback_query.message.edit_text("Загрузка изображения...")

    image_url = await get_image_from_unsplash(category)  # Используем английское слово

    if image_url:
        await callback_query.message.answer_photo(photo=image_url,
                                                  caption=f"Вот изображение по запросу '{categories[category]}'")
    else:
        await callback_query.message.edit_text(
            f"К сожалению, не удалось найти изображение для '{categories[category]}'. Попробуйте другую категорию.")


@dp.message()
async def echo(message: types.Message):
    await message.answer(
        "Извините, я не понял ваш запрос. Пожалуйста, воспользуйтесь кнопками меню для выбора действия.",
        reply_markup=get_main_keyboard())


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())