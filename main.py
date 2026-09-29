import telebot

from config import BOT_TOKEN
from handlers.starting import register_start_handlers


# ==========================================
# 🤖 BOT INITIALIZE
# ==========================================

bot = telebot.TeleBot(BOT_TOKEN)


# ==========================================
# 📌 REGISTER HANDLERS
# ==========================================

register_start_handlers(bot)


# ==========================================
# 🚀 START BOT
# ==========================================

print("🤖 Raunak MM Bot is starting...")

bot.infinity_polling(skip_pending=True)
