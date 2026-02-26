import asyncio
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from telegram.error import TelegramError
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Константы
BOT_TOKEN = os.getenv('BOT_TOKEN')
TARGET_BOT_USERNAME = os.getenv('TARGET_BOT_USERNAME', '@GardenHorizonsBot')
ALLOWED_CREATOR = os.getenv('ALLOWED_CREATOR', '@mellfreezy')

class AutoPosterBot:
    def __init__(self):
        self.application = None
        self.target_channels = []
        self.is_running = False
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        await update.message.reply_text(
            "✅ Бот запущен!\n\n"
            "Добавьте меня в канал как администратора для автоматической публикации.\n"
            "Публикация происходит каждые 5 минут (в :00, :05, :10 и т.д.)"
        )
        
        # Запускаем автопостинг если еще не запущен
        if not self.is_running:
            self.is_running = True
            asyncio.create_task(self.auto_post_loop())
    
    async def get_valid_channels(self):
        """Получение списка каналов где бот админ и создатель канала - @mellfreezy"""
        valid_channels = []
        
        try:
            # Получаем обновления чтобы найти каналы
            updates = await self.application.bot.get_updates()
            
            for update in updates:
                if update.my_chat_member:
                    chat = update.my_chat_member.chat
                    if chat.type in ['channel', 'supergroup']:
                        try:
                            # Проверяем администраторов канала
                            admins = await self.application.bot.get_chat_administrators(chat.id)
                            
                            # Проверяем является ли бот администратором
                            bot_is_admin = any(admin.user.id == self.application.bot.id for admin in admins)
                            
                            # Проверяем создателя канала
                            creator = next((admin for admin in admins if admin.status == 'creator'), None)
                            
                            if bot_is_admin and creator and creator.user.username == ALLOWED_CREATOR.replace('@', ''):
                                if chat.id not in valid_channels:
                                    valid_channels.append(chat.id)
                                    logger.info(f"Добавлен канал: {chat.title} (ID: {chat.id})")
                        except TelegramError as e:
                            logger.error(f"Ошибка при проверке канала {chat.id}: {e}")
        except Exception as e:
            logger.error(f"Ошибка при получении каналов: {e}")
        
        return valid_channels
    
    async def simulate_bot_interaction(self):
        """Симуляция взаимодействия с целевым ботом"""
        try:
            # Создаем симуляцию ответа от бота (в реальности это будет приходить от @GardenHorizonsBot)
            # Здесь мы создаем примерное сообщение с кнопками
            
            # Первое сообщение - "Просмотреть сток"
            stock_message = (
                "🌿 **Garden Horizons Stock**\n\n"
                "📦 Available items:\n"
                "• Seeds - 150 units\n"
                "• Tools - 45 units\n"
                "• Fertilizers - 89 units\n\n"
                "Last updated: " + datetime.now().strftime("%H:%M:%S")
            )
            
            # Второе сообщение после нажатия "Gear"
            gear_message = (
                "⚙️ **Garden Equipment**\n\n"
                "🔧 Available gear:\n"
                "• Shovels - 23 pcs\n"
                "• Rakes - 18 pcs\n"
                "• Watering cans - 31 pcs\n"
                "• Pruners - 15 pcs\n\n"
                "Updated: " + datetime.now().strftime("%H:%M:%S")
            )
            
            return stock_message, gear_message
            
        except Exception as e:
            logger.error(f"Ошибка при симуляции взаимодействия: {e}")
            return None, None
    
    async def post_to_channels(self, message_text: str, channels: list):
        """Отправка сообщения в каналы без инлайн-кнопок"""
        for channel_id in channels:
            try:
                await self.application.bot.send_message(
                    chat_id=channel_id,
                    text=message_text,
                    parse_mode='Markdown'
                )
                logger.info(f"Сообщение отправлено в канал {channel_id}")
            except TelegramError as e:
                logger.error(f"Ошибка при отправке в канал {channel_id}: {e}")
    
    async def wait_until_next_interval(self):
        """Ожидание до следующего 5-минутного интервала"""
        now = datetime.now()
        current_minute = now.minute
        current_second = now.second
        
        # Вычисляем следующий интервал кратный 5
        next_interval = ((current_minute // 5) + 1) * 5
        if next_interval >= 60:
            next_interval = 0
            minutes_to_wait = 60 - current_minute
        else:
            minutes_to_wait = next_interval - current_minute
        
        seconds_to_wait = (minutes_to_wait * 60) - current_second
        
        logger.info(f"Следующая публикация через {seconds_to_wait} секунд ({minutes_to_wait} мин)")
        await asyncio.sleep(seconds_to_wait)
    
    async def auto_post_loop(self):
        """Основной цикл автопостинга"""
        # Ждем до первого интервала
        await self.wait_until_next_interval()
        
        while self.is_running:
            try:
                logger.info("Начало цикла публикации...")
                
                # Получаем валидные каналы
                channels = await self.get_valid_channels()
                
                if not channels:
                    logger.warning("Нет доступных каналов для публикации")
                else:
                    # Симулируем взаимодействие с ботом
                    stock_msg, gear_msg = await self.simulate_bot_interaction()
                    
                    if stock_msg and gear_msg:
                        # Отправляем первое сообщение (сток)
                        await self.post_to_channels(stock_msg, channels)
                        
                        # Небольшая задержка
                        await asyncio.sleep(2)
                        
                        # Отправляем второе сообщение (gear)
                        await self.post_to_channels(gear_msg, channels)
                        
                        logger.info("Цикл публикации завершен успешно")
                    else:
                        logger.error("Не удалось получить сообщения")
                
                # Ждем 5 минут до следующей публикации
                await asyncio.sleep(300)  # 5 минут = 300 секунд
                
            except Exception as e:
                logger.error(f"Ошибка в цикле автопостинга: {e}")
                await asyncio.sleep(60)  # Ждем минуту перед повтором при ошибке
    
    async def my_chat_member_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик изменений статуса бота в чатах"""
        if update.my_chat_member:
            chat = update.my_chat_member.chat
            new_status = update.my_chat_member.new_chat_member.status
            
            if new_status in ['administrator', 'member']:
                logger.info(f"Бот добавлен в {chat.type}: {chat.title} (ID: {chat.id})")
            elif new_status in ['left', 'kicked']:
                logger.info(f"Бот удален из {chat.type}: {chat.title} (ID: {chat.id})")
    
    def run(self):
        """Запуск бота"""
        self.application = Application.builder().token(BOT_TOKEN).build()
        
        # Регистрация обработчиков
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CallbackQueryHandler(self.start))
        
        # Обработчик изменений статуса в чатах
        from telegram.ext import ChatMemberHandler
        self.application.add_handler(
            ChatMemberHandler(self.my_chat_member_handler, ChatMemberHandler.MY_CHAT_MEMBER)
        )
        
        logger.info("Бот запущен!")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    bot = AutoPosterBot()
    bot.run()