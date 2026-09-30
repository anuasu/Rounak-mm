import telebot

from config import BOT_TOKEN

from database.database import init_database

from handlers.starting import register_start_handlers
from handlers.user_message import register_user_message
from handlers.admin_reply import register_admin_reply
from commands.leaderboard import register_leaderboard
from commands.search_user import register_user_search
from commands.deal import register_deal
from commands.deal import register_deal_info



init_database()


bot = telebot.TeleBot(BOT_TOKEN)


register_start_handlers(bot)
register_user_message(bot)
register_admin_reply(bot)
register_leaderboard(bot)
register_user_search(bot)
register_deal(bot)
register_deal_info(bot)

print("🤖 Raunak MM Bot is starting...")

bot.infinity_polling(skip_pending=True)
