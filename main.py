import asyncio
import random
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode

# Импорты
import config
import phrases
from yandex_ai import ai_bot

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== ВАЖНО: сначала инициализация ==========
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()  # <-- ДОЛЖНО БЫТЬ ЗДЕСЬ, ДО КОМАНД!

# Настройки активности
RESPONSE_CHANCE = 0.3  # 30% шанс ответа на обычные сообщения
MIN_MESSAGE_LENGTH = 3  # Минимальная длина сообщения для ответа

# ==================== КОМАНДЫ ====================
# Теперь dp определен, можно писать команды:
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        f"Ну чо, {message.from_user.first_name}, я Бухающий Адекват! 🍻\n\n"
        "Команды:\n"
        "/start - это сообщение\n"
        "/insult [имя] - оскорбить кого-то\n"
        "/story - рассказать матерную историю\n"
        "/ai [текст] - ответ от ИИ\n"
        "/stats - статистика\n"
        "/cache_stats - статистика кэша ИИ\n\n"
        "Реагирую на слова: что, как, почему, нахуй, заебал, ало, татарин, Лиходед, пес, чёрт, салам, пиво, баня\n"
        "На обычные сообщения отвечаю редко (30% шанс)"
    )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await cmd_start(message)

@dp.message(Command("ai"))
async def cmd_ai(message: Message):
    """Команда для ответа через ИИ"""
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        await message.answer("Напиши текст после команды: /ai [текст]")
        return
    
    user_message = args[1]
    
    # Показываем статус "печатает"
    await message.bot.send_chat_action(message.chat.id, "typing")
    
    # Генерируем ответ через ИИ
    ai_response = ai_bot.generate_response(user_message, message.from_user.first_name)
    
    await message.answer(ai_response)

@dp.message(Command("insult"))
async def cmd_insult(message: Message):
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        target = "ты"
    else:
        target = args[1]
    
    insult = random.choice(phrases.INSULTS).format(target=target)
    await message.answer(insult)

@dp.message(Command("story"))
async def cmd_story(message: Message):
    story = random.choice(phrases.STORIES)
    await message.answer(story)

@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    stats_text = (
        "📊 <b>Статистика Бухающего Адеквата:</b>\n\n"
        f"• Фраз в базе: {len(phrases.RANDOM_PHRASES)}\n"
        f"• Оскорблений: {len(phrases.INSULTS)}\n"
        f"• Историй: {len(phrases.STORIES)}\n"
        f"• Триггеров: {len(phrases.TRIGGERS)}\n"
        f"• Шанс ответа: {RESPONSE_CHANCE*100}%\n"
        f"• ИИ: Яндекс GPT 🧠\n\n"
        "Режим: умеренный (только на триггеры + 30% шанс)"
    )
    await message.answer(stats_text, parse_mode=ParseMode.HTML)

@dp.message(Command("cache_stats"))
async def cmd_cache_stats(message: Message):
    """Показать статистику кэша ИИ"""
    try:
        stats = ai_bot.get_stats()
        
        stats_text = (
            "🧠 <b>Статистика ИИ кэша:</b>\n\n"
            f"• Всего запросов: {stats['total_requests']}\n"
            f"• Попаданий в кэш: {stats['cache_hits']}\n"
            f"• Запросов к API: {stats['api_calls']}\n"
            f"• Эффективность кэша: {stats['cache_hit_rate']}\n"
            f"• Размер кэша: {stats['cache_size']} записей\n"
            f"• Размер файла: {stats['cache_file_size']}\n\n"
            "Кэш экономит запросы к Яндекс GPT!"
        )
        await message.answer(stats_text, parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.answer(f"Ошибка получения статистики: {e}")

@dp.message(Command("mode"))
async def cmd_mode(message: Message):
    """Смена режима активности (только для админа)"""
    if message.from_user.id == config.ADMIN_ID:
        args = message.text.split()
        if len(args) > 1:
            mode = args[1].lower()
            if mode == "active":
                global RESPONSE_CHANCE
                RESPONSE_CHANCE = 0.7
                await message.answer("✅ Режим: активный (70% шанс ответа)")
            elif mode == "quiet":
                RESPONSE_CHANCE = 0.1
                await message.answer("✅ Режим: тихий (10% шанс ответа)")
            elif mode == "normal":
                RESPONSE_CHANCE = 0.3
                await message.answer("✅ Режим: нормальный (30% шанс ответа)")
        else:
            await message.answer("Использование: /mode [active|quiet|normal]")
    else:
        await message.answer("❌ Только админ может менять режим!")

# ==================== ОБРАБОТКА ВСЕХ СООБЩЕНИЙ ====================
@dp.message(F.text)
async def handle_all_messages(message: Message):
    user_name = message.from_user.first_name
    text_lower = message.text.lower()
    
    # Пропускаем слишком короткие сообщения
    if len(text_lower) < MIN_MESSAGE_LENGTH:
        return
    
    # 1. Сначала проверяем триггерные слова - ОБЯЗАТЕЛЬНЫЙ ОТВЕТ
    for trigger, responses in phrases.TRIGGERS.items():
        if trigger in text_lower:
            response = random.choice(responses).format(name=user_name)
            await message.answer(response)
            return
    
    # 2. Проверяем, является ли это командой (начинается с /)
    if text_lower.startswith('/'):
        # Команды уже обрабатываются отдельно, пропускаем
        return
    
    # 3. Обычные сообщения - отвечаем с вероятностью RESPONSE_CHANCE
    if random.random() < RESPONSE_CHANCE:
        # Решаем, использовать ИИ или старые фразы
        use_ai = random.random() < 0.4  # 40% шанс на ИИ
        
        if use_ai:
            # Показываем статус "печатает" для ИИ
            await message.bot.send_chat_action(message.chat.id, "typing")
            
            # Генерируем ответ через ИИ
            ai_response = ai_bot.generate_response(message.text, user_name)
            await message.answer(ai_response)
        else:
            # Используем старые фразы
            random_phrase = random.choice(phrases.RANDOM_PHRASES).format(name=user_name)
            await message.answer(random_phrase)
    else:
        # Не отвечаем вообще
        pass

# ==================== РЕАКЦИИ НА СТИКЕРЫ ====================
@dp.message(F.sticker)
async def handle_sticker(message: Message):
    # На стикеры реагируем редко (20% шанс)
    if random.random() < 0.2:
        reactions = [
            f"Чё за стикеры, {message.from_user.first_name}?",
            f"Охуенный стикер, {message.from_user.first_name}!",
            f"{message.from_user.first_name}, иди нахуй со стикерами!",
        ]
        response = random.choice(reactions)
        await message.answer(response)

# ==================== ОБРАБОТКА ГОЛОСОВЫХ ====================
@dp.message(F.voice)
async def handle_voice(message: Message):
    # На голосовые реагируем всегда
    responses = [
        f"Бля, {message.from_user.first_name}, рот закрой!",
        f"Голосовухи не слушаю, {message.from_user.first_name}! Пиши текстом!",
        f"Заебал орать, {message.from_user.first_name}!",
        f"Охуенный голос, {message.from_user.first_name}! Теперь иди нахуй!",
    ]
    response = random.choice(responses)
    await message.answer(response)

# ==================== ЗАПУСК БОТА ====================
async def main():
    logger.info("🤖 Бот 'Бухающий Адекват' запускается...")
    logger.info(f"📊 Режим: умеренный ({RESPONSE_CHANCE*100}% шанс ответа)")
    logger.info(f"🎯 Триггеров: {len(phrases.TRIGGERS)} слов")
    
    # Удаляем вебхук
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запускаем
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())