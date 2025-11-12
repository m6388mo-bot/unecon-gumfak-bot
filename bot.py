import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv
import asyncio

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
UNECON_URL = "https://unecon.ru"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

HUMANITIES_DIRECTIONS = [
    "Лингвистика (Каф. романо-германской филологии и перевода)",
    "Перевод и переводоведение (Каф. английской филологии и перевода)",
    "Английский язык (Каф. английского языка №1/№2)",
    "Восточные языки",
    "Реклама и связи с общественностью",
    "Международные отношения и политология",
    "Регионоведение (зарубежное регионоведение)",
    "Теория и практика массмедиа",
]

FAQ = [
    ("Как подать документы?",
     "Пакет документов: заявление, паспорт, результаты ЕГЭ/аттестат. Сроки и список — на странице Приёмной комиссии."),
    ("Какие вступительные испытания?",
     "Для большинства направлений — результаты ЕГЭ. Некоторые направления могут иметь дополнительные испытания."),
    ("Есть ли общежитие?",
     "Да, университет предоставляет общежитие. Подробности на сайте СПбГЭУ."),
]

CONTACTS_TEXT = (
    "Приёмная комиссия СПбГЭУ\n"
    "Тел.: +7 (812) 458-97-58\n"
    "E-mail: abitura@unecon.ru\n"
    "Адрес: наб. канала Грибоедова, д. 30-32, лит. А, каб. 1039\n\n"
    f"Официальный сайт: {UNECON_URL}"
)

kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📚 Направления")],
        [KeyboardButton(text="❓ FAQ по поступлению"), KeyboardButton(text="📞 Контакты приёмной комиссии")],
        [KeyboardButton(text="🔗 Ссылки на сайт"), KeyboardButton(text="✉️ Обратная связь")],
    ],
    resize_keyboard=True
)

class FeedbackStates(StatesGroup):
    waiting_name = State()
    waiting_contact = State()
    waiting_message = State()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    welcome = (
        "Привет! Я — бот для абитуриентов Гуманитарного факультета СПбГЭУ 👋\n\n"
        "Могу показать направления, ответить на часто задаваемые вопросы, дать контакты приёмной комиссии "
        "и принять твоё сообщение.\n\nВыбирай пункт меню ниже."
    )
    await message.answer(welcome, reply_markup=kb)

@dp.message()
async def text_handler(message: types.Message, state: FSMContext):
    text = message.text.strip()

    if text == "📚 Направления":
        txt = "Направления гуманитарного факультета:\n\n"
        for i, d in enumerate(HUMANITIES_DIRECTIONS, start=1):
            txt += f"{i}. {d}\n"
        await message.answer(txt)

    elif text == "❓ FAQ по поступлению":
        out = "FAQ — часто задаваемые вопросы:\n\n"
        for q, a in FAQ:
            out += f"• *{q}*\n{a}\n\n"
        await message.answer(out, parse_mode="Markdown")

    elif text == "📞 Контакты приёмной комиссии":
        await message.answer(CONTACTS_TEXT)

    elif text == "🔗 Ссылки на сайт":
        links = (
            f"Официальный сайт: {UNECON_URL}\n"
            "Страница факультета: https://unecon.ru/fakultety/gumanitarnyj-fakultet/\n"
            "Приёмная комиссия: https://unecon.ru/education/\n"
            "Личный кабинет абитуриента: https://priem.unecon.ru"
        )
        await message.answer(links)

    elif text == "✉️ Обратная связь":
        await state.set_state(FeedbackStates.waiting_name)
        await message.answer("Оставь, пожалуйста, своё имя.")

    elif await state.get_state() == FeedbackStates.waiting_name:
        await state.update_data(name=message.text.strip())
        await state.set_state(FeedbackStates.waiting_contact)
        await message.answer("Оставь свой контакт (телефон или e-mail).")

    elif await state.get_state() == FeedbackStates.waiting_contact:
        await state.update_data(contact=message.text.strip())
        await state.set_state(FeedbackStates.waiting_message)
        await message.answer("Опиши свой вопрос или сообщение.")

    elif await state.get_state() == FeedbackStates.waiting_message:
        data = await state.get_data()
        name = data.get("name")
        contact = data.get("contact")
        msg = message.text.strip()

        summary = f"Сообщение от {name}\nКонтакт: {contact}\nТекст:\n{msg}"

        if ADMIN_CHAT_ID:
            try:
                await bot.send_message(int(ADMIN_CHAT_ID), summary)
            except:
                pass

        with open("feedbacks.txt", "a", encoding="utf-8") as f:
            f.write(summary + "\n---\n")

        await message.answer("Спасибо! Сообщение отправлено. 😊")
        await state.clear()

    else:
        await message.answer("Выбери пункт меню, пожалуйста 😊")

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
