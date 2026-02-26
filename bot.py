import asyncio
import logging
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
import os
from dotenv import load_dotenv

load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Константы из .env
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
SESSION_NAME = os.getenv('SESSION_NAME', 'my_account')
TARGET_BOT = os.getenv('TARGET_BOT', 'GardenHorizonsBot')
ALLOWED_CREATOR = os.getenv('ALLOWED_CREATOR', 'mellfreezy')

# Хранилище
registered_channels = set()
last_stock_message = None
last_gear_message = None
waiting_for_response = False

# Создаем клиент
app = Client(SESSION_NAME, api_id=API_ID, api_hash=API_HASH)


async def get_valid_channels():
    """Получение каналов где создатель - разрешенный пользователь"""
    valid = []
    
    async for dialog in app.get_dialogs():
        if dialog.chat.type in ["channel", "supergroup"]:
            try:
                async for member in app.get_chat_members(dialog.chat.id, filter="administrators"):
                    if member.status.name == "OWNER":
                        if member.user.username and member.user.username.lower() == ALLOWED_CREATOR.lower():
                            valid.append(dialog.chat.id)
                            logger.info(f"✅ Канал найден: {dialog.chat.title}")
                        break
            except Exception as e:
                logger.debug(f"Пропуск {dialog.chat.id}: {e}")
    
    return valid


async def remove_inline_keyboard(text: str) -> str:
    """Возвращает текст сообщения (кнопки не копируются при отправке текста)"""
    return text if text else ""


async def send_to_channels(text: str):
    """Отправка сообщения в каналы"""
    channels = await get_valid_channels()
    
    if not channels:
        logger.warning("Нет доступных каналов")
        return
    
    for channel_id in channels:
        try:
            await app.send_message(channel_id, text)
            logger.info(f"✅ Отправлено в канал {channel_id}")
            await asyncio.sleep(1)
        except FloodWait as e:
            logger.warning(f"FloodWait: ждем {e.value} сек")
            await asyncio.sleep(e.value)
        except Exception as e:
            logger.error(f"Ошибка отправки в {channel_id}: {e}")


async def interact_with_target_bot():
    """Взаимодействие с целевым ботом"""
    global waiting_for_response, last_stock_message, last_gear_message
    
    try:
        logger.info(f"🤖 Отправляем /start в @{TARGET_BOT}")
        await app.send_message(TARGET_BOT, "/start")
        waiting_for_response = "start"
        
    except Exception as e:
        logger.error(f"Ошибка взаимодействия с ботом: {e}")


@app.on_message(filters.chat(TARGET_BOT) & filters.incoming)
async def handle_bot_response(client: Client, message: Message):
    """Обработка ответов от целевого бота"""
    global waiting_for_response, last_stock_message, last_gear_message
    
    logger.info(f"📨 Получено сообщение от @{TARGET_BOT}")
    
    if message.reply_markup:
        # Ищем кнопку "Просмотреть сток" или похожую
        for row in message.reply_markup.inline_keyboard:
            for button in row:
                button_text = button.text.lower()
                
                if waiting_for_response == "start":
                    # Ищем кнопку со стоком
                    if "сток" in button_text or "stock" in button_text or "просмотр" in button_text:
                        logger.info(f"🔘 Нажимаем кнопку: {button.text}")
                        await asyncio.sleep(1)
                        
                        if button.callback_data:
                            await message.click(button.callback_data)
                        else:
                            await message.click(button.text)
                        
                        waiting_for_response = "stock"
                        return
                
                elif waiting_for_response == "stock":
                    # Это ответ на "Просмотреть сток" - сохраняем и ищем Gear
                    last_stock_message = message.text or message.caption or ""
                    
                    if last_stock_message:
                        logger.info("📦 Получен сток, отправляем в каналы")
                        await send_to_channels(last_stock_message)
                    
                    # Ищем кнопку Gear
                    if "gear" in button_text:
                        logger.info(f"🔘 Нажимаем кнопку: {button.text}")
                        await asyncio.sleep(1)
                        
                        if button.callback_data:
                            await message.click(button.callback_data)
                        else:
                            await message.click(button.text)
                        
                        waiting_for_response = "gear"
                        return
    
    # Если это ответ на gear или просто текстовое сообщение
    if waiting_for_response == "stock" and not message.reply_markup:
        last_stock_message = message.text or message.caption or ""
        if last_stock_message:
            logger.info("📦 Получен сток, отправляем в каналы")
            await send_to_channels(last_stock_message)
        waiting_for_response = None
        
    elif waiting_for_response == "gear":
        last_gear_message = message.text or message.caption or ""
        if last_gear_message:
            logger.info("⚙️ Получен gear, отправляем в каналы")
            await send_to_channels(last_gear_message)
        waiting_for_response = None
    
    # Если есть кнопка Gear в текущем сообщении
    if message.reply_markup and waiting_for_response == "stock":
        for row in message.reply_markup.inline_keyboard:
            for button in row:
                if "gear" in button.text.lower():
                    # Сохраняем текущее сообщение как сток
                    last_stock_message = message.text or message.caption or ""
                    if last_stock_message:
                        await send_to_channels(last_stock_message)
                    
                    logger.info(f"🔘 Нажимаем Gear: {button.text}")
                    await asyncio.sleep(1)
                    
                    if button.callback_data:
                        await message.click(button.callback_data)
                    else:
                        await message.click(button.text)
                    
                    waiting_for_response = "gear"
                    return


async def wait_until_next_interval():
    """Ожидание до следующего 5-минутного интервала"""
    now = datetime.now()
    current_minute = now.minute
    current_second = now.second
    current_microsecond = now.microsecond
    
    # Следующий интервал кратный 5
    next_interval = ((current_minute // 5) + 1) * 5
    
    if next_interval >= 60:
        minutes_to_wait = 60 - current_minute
    else:
        minutes_to_wait = next_interval - current_minute
    
    seconds_to_wait = (minutes_to_wait * 60) - current_second - (current_microsecond / 1000000)
    
    if seconds_to_wait <= 0:
        seconds_to_wait = 300  # 5 минут
    
    next_time = datetime.now().replace(
        minute=(current_minute // 5 + 1) * 5 % 60,
        second=0,
        microsecond=0
    )
    logger.info(f"⏰ Следующая публикация примерно в {next_time.strftime('%H:%M')}")
    
    await asyncio.sleep(seconds_to_wait)


async def auto_post_loop():
    """Основной цикл автопостинга"""
    await asyncio.sleep(5)  # Даем время на инициализацию
    
    logger.info("🚀 Автопостинг запущен!")
    
    # Ждем до первого интервала
    await wait_until_next_interval()
    
    while True:
        try:
            logger.info(f"=== 🔄 Цикл публикации {datetime.now().strftime('%H:%M:%S')} ===")
            await interact_with_target_bot()
            
        except Exception as e:
            logger.error(f"Ошибка в цикле: {e}")
        
        # Ждем 5 минут
        await asyncio.sleep(300)


@app.on_message(filters.command("start") & filters.me)
async def my_start(client: Client, message: Message):
    """Ручной запуск"""
    await message.reply("✅ Userbot активен!\nАвтопостинг работает каждые 5 минут.")


async def main():
    """Главная функция"""
    await app.start()
    logger.info(f"✅ Userbot запущен как @{(await app.get_me()).username}")
    
    # Запускаем автопостинг
    asyncio.create_task(auto_post_loop())
    
    # Держим бота активным
    await asyncio.Event().wait()


if __name__ == '__main__':
    app.run(main())
