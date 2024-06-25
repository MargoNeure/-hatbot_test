import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import config

API_TOKEN = config.token

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Создаем клавиатуру

def get_keyboard():
    keyboard = [
        [KeyboardButton(text="/start")],
        [KeyboardButton(text="/ура")],
        [KeyboardButton(text="/info")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer("Привет! Я эхобот на aiogram 3. Отправь мне любое сообщение, и я повторю его.", reply_markup=get_keyboard())

@dp.message(Command("ура"))
async def send_ura(message: types.Message):
    await message.answer("УРАААА! Я эхобот на aiogram 3. Отправь мне любое сообщение, и я повторю его.", reply_markup=get_keyboard())

@dp.message(Command("info"))
async def botinfo(message: types.Message):
    await message.answer("Информация по этому боту не заполнена", reply_markup=get_keyboard())

@dp.message()
async def echo(message: types.Message):
    await message.answer(message.text, reply_markup=get_keyboard())

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
