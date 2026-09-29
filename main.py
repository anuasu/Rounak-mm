import telebot

from config import BOT_TOKEN
from handlers.starting import register_start_handlers



init_database()

bot = telebot.TeleBot(BOT_TOKEN)

register_start_handlers(bot)

print("🤖 Raunak MM Bot is starting...")

bot.infinity_polling(skip_pending=True)
