"""
Telegram-бот для привлечения курьеров-партнёров Яндекс Еды — Санкт-Петербург
Запуск: python bot.py
"""

import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    KeyboardButton, Message, ReplyKeyboardMarkup,
    ReplyKeyboardRemove, contact
)

from config import BOT_TOKEN, ADMIN_CHAT_ID

# ── Логирование ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Инициализация ─────────────────────────────────────────────────────────────
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ── Состояния FSM ─────────────────────────────────────────────────────────────
class Form(StatesGroup):
    city        = State()
    city_other  = State()
    age         = State()
    transport   = State()
    schedule    = State()
    documents   = State()
    name        = State()
    phone       = State()
    consent     = State()


# ── Вспомогательные клавиатуры ────────────────────────────────────────────────
def kb(*labels, resize=True, one_time=True):
    """Быстрое создание ReplyKeyboardMarkup из списка строк."""
    buttons = [[KeyboardButton(text=t)] for t in labels]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=resize,
                               one_time_keyboard=one_time)


def kb_phone():
    """Клавиатура с кнопкой «Отправить номер телефона»."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Отправить номер телефона",
                                  request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True,
    )


KB_START = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚀 Хочу попробовать")],
        [KeyboardButton(text="💰 Узнать условия")],
        [KeyboardButton(text="❓ Частые вопросы")],
    ],
    resize_keyboard=True,
)

KB_CITY      = kb("Санкт-Петербург", "Другой город")
KB_AGE       = kb("Да, мне 18+", "Нет, мне меньше 18")
KB_TRANSPORT = kb("🚶 Пешком", "🚲 Велосипед", "🛴 Самокат", "🚗 Авто", "Пока не знаю")
KB_SCHEDULE  = kb("По вечерам", "В выходные", "В свободное время", "Хочу чаще", "Пока не знаю")
KB_DOCS      = kb("Паспорт РФ", "Документы ЕАЭС", "Патент / другие", "Хочу уточнить")
KB_CONSENT   = kb("✅ Согласен", "◀️ Назад")
KB_BACK      = kb("🔄 Вернуться в начало")
KB_FINAL     = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚀 Перейти к регистрации")],
        [KeyboardButton(text="👤 Написать человеку")],
        [KeyboardButton(text="❓ Частые вопросы")],
    ],
    resize_keyboard=True,
)


# ── FAQ ───────────────────────────────────────────────────────────────────────
FAQ_TEXT = """
❓ <b>Частые вопросы</b>

<b>Можно ли совмещать с учёбой или основной занятостью?</b>
Да — вы сами выбираете режим доставок и выходите на слоты, когда это удобно.

<b>Можно ли доставлять рядом с домом?</b>
Да, можно выбирать удобные районы и зоны в Санкт-Петербурге.

<b>Нужен ли велосипед или самокат?</b>
Нет, возможен пеший формат. Конкретный вариант подбирается при подключении к сервису.

<b>Каков доход курьера-партнёра?</b>
Вознаграждение зависит от количества заказов, времени выхода на слоты и формата доставки. Предусмотрена минимальная оплата за слот, бонусы и чаевые.

<b>Это официальный бот Яндекс Еды?</b>
Нет, это бот партнёрского привлечения. Мы помогаем разобраться с подключением к сервису через партнёрскую ссылку.
""".strip()

CONDITIONS_TEXT = """
💡 <b>Условия сотрудничества</b>

✅ <b>Минимальная оплата за слот</b> — даже если заказов не было
🛡 <b>Страхование</b> — во время доставки и в личное время
⚖️ <b>Юридическая поддержка</b> — до 3 консультаций в месяц бесплатно
🎁 <b>Чаевые</b> — 100% остаются у курьера-партнёра
📈 <b>Повышенные коэффициенты</b> — бонусы за активность и час пик
⏱ <b>Оплата ожидания</b> — если заказ в ресторане ещё не готов

Для старта нужны: возраст 18+, смартфон, документы.
Транспорт — по желанию.
""".strip()


# ── /start ─────────────────────────────────────────────────────────────────────
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Привет 👋\n\n"
        "Я помогу разобраться, подойдёт ли вам формат доставки заказов "
        "в Санкт-Петербурге.\n\n"
        "Здесь можно:\n"
        "🚀 узнать условия подключения к сервису\n"
        "🛵 выбрать удобный формат доставки\n"
        "📍 понять, можно ли выходить на слоты рядом с домом\n"
        "📲 получить инструкцию по регистрации\n\n"
        "Это займёт около 1 минуты.",
        reply_markup=KB_START,
    )


# Кнопка «Вернуться в начало» из любого места
@dp.message(F.text == "🔄 Вернуться в начало")
async def back_to_start(message: Message, state: FSMContext):
    await cmd_start(message, state)


# ── УСЛОВИЯ ───────────────────────────────────────────────────────────────────
@dp.message(F.text == "💰 Узнать условия")
async def show_conditions(message: Message):
    await message.answer(CONDITIONS_TEXT, parse_mode="HTML",
                         reply_markup=KB_START)


# ── FAQ ────────────────────────────────────────────────────────────────────────
@dp.message(F.text == "❓ Частые вопросы")
async def show_faq(message: Message):
    await message.answer(FAQ_TEXT, parse_mode="HTML", reply_markup=KB_START)


# ── ШАГ 1: ГОРОД ──────────────────────────────────────────────────────────────
@dp.message(F.text == "🚀 Хочу попробовать")
async def ask_city(message: Message, state: FSMContext):
    await state.set_state(Form.city)
    await message.answer(
        "В каком городе вы хотите выходить на доставку?",
        reply_markup=KB_CITY,
    )


@dp.message(Form.city, F.text == "Санкт-Петербург")
async def city_spb(message: Message, state: FSMContext):
    await state.update_data(city="Санкт-Петербург")
    await state.set_state(Form.age)
    await message.answer("Отлично, начнём со СПб 👍\n\nВам уже есть 18 лет?",
                         reply_markup=KB_AGE)


@dp.message(Form.city, F.text == "Другой город")
async def city_other(message: Message, state: FSMContext):
    await state.set_state(Form.city_other)
    await message.answer(
        "Напишите ваш город — подскажу, можно ли рассмотреть подключение там.",
        reply_markup=ReplyKeyboardRemove(),
    )


@dp.message(Form.city_other)
async def city_other_input(message: Message, state: FSMContext):
    city = message.text.strip()
    await state.update_data(city=city)
    await state.set_state(Form.age)
    await message.answer(
        f"Понял, {city}. Уточним детали — вам уже есть 18 лет?",
        reply_markup=KB_AGE,
    )


# ── ШАГ 2: ВОЗРАСТ ────────────────────────────────────────────────────────────
@dp.message(Form.age, F.text == "Да, мне 18+")
async def age_ok(message: Message, state: FSMContext):
    await state.update_data(age="18+")
    await state.set_state(Form.transport)
    await message.answer("Какой формат доставки вам ближе?",
                         reply_markup=KB_TRANSPORT)


@dp.message(Form.age, F.text == "Нет, мне меньше 18")
async def age_no(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Пока подключение невозможно — для старта нужен возраст от 18 лет.\n\n"
        "Можете вернуться к боту позже 👍",
        reply_markup=KB_BACK,
    )


# ── ШАГ 3: ТРАНСПОРТ ──────────────────────────────────────────────────────────
TRANSPORT_OPTIONS = {"🚶 Пешком", "🚲 Велосипед", "🛴 Самокат",
                     "🚗 Авто", "Пока не знаю"}


@dp.message(Form.transport, F.text.in_(TRANSPORT_OPTIONS))
async def ask_schedule(message: Message, state: FSMContext):
    await state.update_data(transport=message.text)
    await state.set_state(Form.schedule)
    await message.answer(
        "Хорошо. Когда вам было бы удобно выходить на доставку?",
        reply_markup=KB_SCHEDULE,
    )


# ── ШАГ 4: РЕЖИМ ДОСТАВОК ─────────────────────────────────────────────────────
SCHEDULE_OPTIONS = {"По вечерам", "В выходные", "В свободное время",
                    "Хочу чаще", "Пока не знаю"}


@dp.message(Form.schedule, F.text.in_(SCHEDULE_OPTIONS))
async def ask_documents(message: Message, state: FSMContext):
    await state.update_data(schedule=message.text)
    await state.set_state(Form.documents)
    await message.answer(
        "Понял. Партнёрство с Яндекс Едой можно совмещать с учёбой, "
        "основной занятостью или другими делами.\n\n"
        "Какие документы у вас есть?",
        reply_markup=KB_DOCS,
    )


# ── ШАГ 5: ДОКУМЕНТЫ ──────────────────────────────────────────────────────────
DOCS_OPTIONS = {"Паспорт РФ", "Документы ЕАЭС",
                "Патент / другие", "Хочу уточнить"}


@dp.message(Form.documents, F.text.in_(DOCS_OPTIONS))
async def ask_name(message: Message, state: FSMContext):
    await state.update_data(documents=message.text)
    await state.set_state(Form.name)
    await message.answer(
        "Список документов для оформления зависит от формата сотрудничества — "
        "уточним на следующем шаге.\n\n"
        "Оставьте, пожалуйста, имя и номер телефона, чтобы мы могли помочь "
        "с подключением, если возникнут вопросы.\n\n"
        "Сначала напишите ваше <b>имя</b>:",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove(),
    )


# ── ШАГ 6: ИМЯ ────────────────────────────────────────────────────────────────
@dp.message(Form.name)
async def ask_phone(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("Пожалуйста, введите корректное имя.")
        return
    await state.update_data(name=name)
    await state.set_state(Form.phone)
    await message.answer(
        f"Приятно познакомиться, {name}! 👋\n\n"
        "Теперь отправьте номер телефона — нажмите кнопку ниже "
        "или введите вручную в формате +7XXXXXXXXXX.",
        reply_markup=kb_phone(),
    )


# ── ШАГ 7: ТЕЛЕФОН ────────────────────────────────────────────────────────────
@dp.message(Form.phone, F.contact)
async def phone_from_contact(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone
    await state.update_data(phone=phone)
    await state.set_state(Form.consent)
    await message.answer(
        "Нажимая кнопку ниже, вы соглашаетесь на обработку ваших данных "
        "для связи по вопросу подключения к сервису.",
        reply_markup=KB_CONSENT,
    )


@dp.message(Form.phone)
async def phone_manual(message: Message, state: FSMContext):
    phone = message.text.strip()
    # Простая валидация: должен содержать хотя бы 10 цифр
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) < 10:
        await message.answer(
            "Пожалуйста, введите корректный номер телефона, "
            "например +79001234567.",
            reply_markup=kb_phone(),
        )
        return
    await state.update_data(phone=phone)
    await state.set_state(Form.consent)
    await message.answer(
        "Нажимая кнопку ниже, вы соглашаетесь на обработку ваших данных "
        "для связи по вопросу подключения к сервису.",
        reply_markup=KB_CONSENT,
    )


# ── ШАГ 8: СОГЛАСИЕ ───────────────────────────────────────────────────────────
@dp.message(Form.consent, F.text == "◀️ Назад")
async def consent_back(message: Message, state: FSMContext):
    await state.set_state(Form.phone)
    await message.answer("Введите номер телефона:", reply_markup=kb_phone())


@dp.message(Form.consent, F.text == "✅ Согласен")
async def consent_ok(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    # Финальное сообщение пользователю
    await message.answer(
        "Спасибо, заявка сохранена ✅\n\n"
        "Дальше можно перейти к регистрации.\n"
        "После перехода следуйте инструкции на странице подключения.\n\n"
        "Если возникнут вопросы — напишите, я помогу разобраться.",
        reply_markup=KB_FINAL,
    )

    # Уведомление администратору
    await notify_admin(data, message.from_user)


# ── ШАГ 9: ФИНАЛ — кнопки после заявки ───────────────────────────────────────
@dp.message(F.text == "🚀 Перейти к регистрации")
async def go_register(message: Message):
    # TODO: https://reg.eda.yandex.ru/?advertisement_campaign=forms_for_agents&user_invite_code=acd568205bad49acafccbcf7ace44ca5&utm_content=blank
    await message.answer(
        "Переходите по ссылке для подключения к сервису:\n"
        "👉 https://reg.eda.yandex.ru/?advertisement_campaign=forms_for_agents&user_invite_code=acd568205bad49acafccbcf7ace44ca5&utm_content=blank  ← замените на свою партнёрскую ссылку\n\n"
        "Следуйте инструкции на странице — там всё подробно описано.\n"
        "Если что-то непонятно — напишите сюда, помогу 👍",
        reply_markup=KB_FINAL,
    )


@dp.message(F.text == "👤 Написать человеку")
async def write_to_human(message: Message):
    # TODO: @qsewer
    await message.answer(
        "Напишите напрямую: @qsewer\n\n"  # ← замените
        "Отвечу в ближайшее время 👍",
        reply_markup=KB_FINAL,
    )


# ── УВЕДОМЛЕНИЕ АДМИНИСТРАТОРУ ────────────────────────────────────────────────
async def notify_admin(data: dict, user):
    if not ADMIN_CHAT_ID:
        return
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    tg_username = f"@{user.username}" if user.username else f"id:{user.id}"

    text = (
        "🚀 <b>Новый лид!</b>\n\n"
        f"👤 <b>Имя:</b> {data.get('name', '—')}\n"
        f"📱 <b>Телефон:</b> {data.get('phone', '—')}\n"
        f"✈️ <b>Telegram:</b> {tg_username}\n"
        f"📍 <b>Город:</b> {data.get('city', '—')}\n"
        f"🎂 <b>Возраст:</b> 18+\n"
        f"🚗 <b>Формат:</b> {data.get('transport', '—')}\n"
        f"🕐 <b>Режим доставок:</b> {data.get('schedule', '—')}\n"
        f"📄 <b>Документы:</b> {data.get('documents', '—')}\n"
        f"📅 <b>Дата:</b> {now}\n\n"
        f"🏷 <b>Статус:</b> новый лид"
    )
    try:
        await bot.send_message(ADMIN_CHAT_ID, text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Не удалось отправить уведомление админу: {e}")


# ── ЗАПУСК ────────────────────────────────────────────────────────────────────
async def main():
    logger.info("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
