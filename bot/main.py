import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.database import CareerDB
from config import API_TOKEN, DB_NAME, QUESTIONS, CAREERS

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

db = CareerDB(DB_NAME) 

@dp.message(Command("start"))
async def start_test(message: types.Message):
    user_id = message.from_user.id
    db.save_user_session(user_id, tags=[], current=0)

    await message.answer(
        "🎯 Привет! Я помогу тебе выбрать профессию, которая тебе подойдётся по-настоящему.\n"
        "Отвечай на пару простых вопросов — и узнаешь, кем тебе стоит попробовать стать! "
    )
    await send_question(user_id)

async def send_question(user_id: int):
    session = db.get_user_session(user_id)
    if session is None:
        session = {"tags": [], "current": 0}
        db.save_user_session(user_id, session["tags"], session["current"])

    index = session["current"]
    if index >= len(QUESTIONS):
        db.save_user_session(user_id, session["tags"], session["current"]) 
        careers = db.get_best_careers(user_id)

        if careers:
            result = "🎯 Тебе могут подойти:\n\n"
            for name, desc in careers:
                result += f"🔹 <b>{name}</b>\n{desc}\n\n"
        else:
            result = "😕 Не удалось подобрать профессию. Попробуй позже или измени ответы."

        await bot.send_message(user_id, result, parse_mode='HTML')
        db.clear_user_session(user_id)
        return

    q = QUESTIONS[index]

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=option["text"], callback_data=option["text"])]
            for option in q["options"]
        ]
    )

    await bot.send_message(user_id, f"🧠 {q['text']}", reply_markup=keyboard)

@dp.callback_query()
async def handle_answer(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    session = db.get_user_session(user_id)
    if not session:
        await callback.answer("Сначала введи /start")
        return

    current_q = session["current"]
    if current_q >= len(QUESTIONS):
        await callback.answer("Тест уже завершён")
        return

    q = QUESTIONS[current_q]

    for option in q["options"]:
        if option["text"] == callback.data:
            session["tags"].extend(option["tags"])

    session["current"] += 1
    db.save_user_session(user_id, session["tags"], session["current"])

    await callback.answer("✅ Ответ принят")
    await send_question(user_id)

async def main():
    db.load_careers(CAREERS)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
