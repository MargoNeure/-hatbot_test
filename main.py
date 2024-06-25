from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio


API_TOKEN = config.token

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


class ChoosePen(StatesGroup):
    waiting_for_purpose = State()
    waiting_for_ink_color = State()
    waiting_for_line_thickness = State()


@dp.message(Command(commands=['start', 'help']))
async def send_welcome(message: types.Message):
    await message.reply("Привет! Я помогу вам выбрать идеальную ручку. Начнем? Напишите /choose")


@dp.message(Command("choose"))
async def cmd_choose(message: types.Message, state: FSMContext):
    await state.set_state(ChoosePen.waiting_for_purpose)
    await message.reply("Для каких целей вам нужна ручка? (работа/учеба/творчество)")


@dp.message(ChoosePen.waiting_for_purpose)
async def process_purpose(message: types.Message, state: FSMContext):
    await state.update_data(purpose=message.text.lower())
    await state.set_state(ChoosePen.waiting_for_ink_color)
    await message.reply("Какой цвет чернил вы предпочитаете? (синий/черный/красный)")


@dp.message(ChoosePen.waiting_for_ink_color)
async def process_ink_color(message: types.Message, state: FSMContext):
    await state.update_data(ink_color=message.text.lower())
    await state.set_state(ChoosePen.waiting_for_line_thickness)
    await message.reply("Какую толщину линии вы предпочитаете? (тонкая/средняя/толстая)")


@dp.message(ChoosePen.waiting_for_line_thickness)
async def process_line_thickness(message: types.Message, state: FSMContext):
    await state.update_data(line_thickness=message.text.lower())

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

    await message.reply(
        f"На основе ваших предпочтений, я рекомендую следующую ручку:\n{recommendation}\n\nЕсли вы хотите узнать о других моделях или у вас есть дополнительные вопросы, пожалуйста, дайте мне знать.")
    await state.clear()


@dp.message()
async def echo(message: types.Message):
    await message.answer(message.text)


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())