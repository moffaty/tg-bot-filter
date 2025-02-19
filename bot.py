import logging
import asyncio
import json
import os
import re
from aiogram import Bot, Dispatcher
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ChatMemberAdministrator,
    ChatMemberOwner,
)
from aiogram.filters import CommandStart, Command
from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv


class ChangeWordsState(StatesGroup):
    waiting_for_words = State()


router = Router()

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
DATA_FILE = "bot_data.json"

bot = Bot(token=TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)
waiting_for_words = {}


async def is_admin(chat_id: int, user_id: int) -> bool:
    chat_member = await bot.get_chat_member(chat_id, user_id)
    return chat_member.status not in ["creator", "administrator"]


# 📂 Функции для работы с файлами
def load_data():
    """Загружает данные из файла JSON"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return {"filter": [], "admins": []}


def save_data(data, file):
    """Сохраняет данные в JSON"""
    with open(file, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


config = load_data()


# 📌 Главное меню
def main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📜 Список запрещенных слов"),
                KeyboardButton(text="✒️ Изменить список запрещенных слов"),
            ],
        ],
        resize_keyboard=True,
    )
    return keyboard


# 🎛 Команда /start
@router.message(CommandStart())
async def start_command(message: Message):
    """Приветствие + меню"""
    if await is_admin(message.chat.id, message.from_user.id):
        await message.reply("У вас недостаточно прав.")
        return

    await message.answer(
        "Привет! Я фильтрую сообщения в чатах.\nВыберите действие:",
        reply_markup=main_menu(),
    )


# 🎛 Команда /menu
@router.message(Command("menu"))
async def menu_command(message: Message):
    """Показывает меню"""
    if await is_admin(message.chat.id, message.from_user.id):
        await message.reply("У вас недостаточно прав.")
        return

    await message.answer("Выберите действие:", reply_markup=main_menu())


# 📜 Список чатов
@router.message(lambda message: message.text == "📜 Список запрещенных слов")
async def list_words(message: Message):
    """Отправляет список запрещенных слов"""
    if await is_admin(message.chat.id, message.from_user.id):
        await message.reply("У вас недостаточно прав.")
        return

    word_list = (
        "\n".join([f"→ {word}" for word in config["filter"]])
        if config["filter"]
        else "Список пуст."
    )
    await message.answer(f"📜 Запрещенные слова: \n{word_list}", parse_mode="HTML")


# ✒️ Изменить список запрещенных слов
@router.message(F.text == "✒️ Изменить список запрещенных слов")
async def change_words(message: types.Message, state: FSMContext):
    """Запрашивает новый список слов."""
    if await is_admin(message.chat.id, message.from_user.id):
        await message.reply("У вас недостаточно прав.")
        return

    await message.answer("Введите список запрещенных слов через запятую")
    await state.set_state(ChangeWordsState.waiting_for_words)  # Устанавливаем состояние


@router.message(ChangeWordsState.waiting_for_words)
async def process_change_words(message: types.Message, state: FSMContext):
    """Обрабатывает введенный список слов."""
    new_words = message.text
    config["filter"] = [word.strip() for word in new_words.split(",") if word.strip()]
    save_data(config, DATA_FILE)

    await message.answer(f"Новый список запрещенных слов: {config['filter']}")
    await state.clear()


# 📌 Фильтр сообщений
@router.message()
async def filter_messages(message: Message):
    """Проверяет сообщения на запрещённые слова"""
    if any(word in message.text.lower() for word in set(config["filter"])):
        found_words = [
            word for word in set(config["filter"]) if word in message.text.lower()
        ]

        chat_id = str(message.chat.id)
        if chat_id.startswith("-100"):
            chat_id = int(chat_id[4:])
        chat_link = f"<a href='https://t.me/{message.chat.username or f'c/{abs(chat_id)}'}'>{message.chat.title}</a>"
        message_link = f"<a href='https://t.me/c/{abs(chat_id)}/{message.message_id}'>Открыть сообщение</a>"

        highlighted_text = message.text
        for word in found_words:
            highlighted_text = re.sub(
                rf"\b{re.escape(word)}\b",
                lambda match: f"<b><u>{match.group()}</u></b>",
                highlighted_text,
                flags=re.IGNORECASE,
            )

        chat_admins = await bot.get_chat_administrators(message.chat.id)
        for admin in chat_admins:
            if (
                isinstance(admin, (ChatMemberAdministrator, ChatMemberOwner))
                and not admin.user.is_bot
            ):
                await bot.send_message(
                    admin.user.id,
                    f"⚠️ В чате {chat_link} найдено запрещённое слово:\n\n"
                    f"👤 От: {message.from_user.full_name} (@{message.from_user.username})\n"
                    f"📍 Чат: {chat_link}\n"
                    f"💬 Сообщение: {highlighted_text}\n\n"
                    f"🔗 {message_link}",
                    parse_mode="HTML",
                )


async def main():
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
