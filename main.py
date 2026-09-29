import telebot

from config import BOT_TOKEN
from handlers.starting import
from handlers.user_message import register_user_message register_start_handlers
from handlers.admin_reply import register_admin_reply


init_database()

bot = telebot.TeleBot(BOT_TOKEN)

register_start_handlers(bot)
register_user_message(bot)
register_admin_reply(bot)


print("🤖 Raunak MM Bot is starting...")

bot.infinity_polling(skip_pending=True)
