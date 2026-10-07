import telebot

from config import BOT_TOKEN

from database.database import init_database

from handlers.starting import register_start_handlers
from handlers.user_message import register_user_message
from handlers.admin_reply import register_admin_reply

from commands.leaderboard import register_leaderboard
from commands.search_user import register_user_search
from commands.deal import register_deal
from commands.removedeal import register_removedeal

from commands.mm_fee import register_mm_fee
from commands.qr import register_qr
from commands.hold import register_hold
from commands.voucher import register_voucher
from commands.form import register_form

from commands.admin_panel import (
    register_admin_panel,
    start_automatic_backup
)

from commands.clean import (
    register_clean,
    install_message_tracker
)


from commands.release import register_release
from commands.refund import register_refund



from commands.split import (
    register_split,
    register_split_input
)




init_database()

bot = telebot.TeleBot(
    BOT_TOKEN
)



install_message_tracker(bot)


register_split(bot)

register_split_input(bot)


register_start_handlers(bot)

register_user_message(bot)

register_admin_reply(bot)



register_leaderboard(bot)

register_user_search(bot)



register_deal(bot)

register_removedeal(bot)



register_mm_fee(bot)

register_qr(bot)

register_hold(bot)


register_release(bot)

register_refund(bot)

register_voucher(bot)

register_form(bot)



register_admin_panel(bot)

start_automatic_backup(bot)




register_clean(bot)



print(
    "🤖 Rounak MM Bot is starting..."
)


bot.infinity_polling(
    skip_pending=True
)
