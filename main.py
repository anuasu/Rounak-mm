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
from commands.payment import register_payment
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

# ==========================================
# NORMAL RELEASE / REFUND
# ==========================================

from commands.release import register_release
from commands.refund import register_refund

# ==========================================
# SPLIT
# ==========================================

from commands.split import (
    register_split,
    register_split_input
)


# ==========================================
# DATABASE
# ==========================================

init_database()


# ==========================================
# BOT
# ==========================================

bot = telebot.TeleBot(
    BOT_TOKEN
)


# ==========================================
# CLEAN MESSAGE TRACKER
# ==========================================

install_message_tracker(bot)


# ==========================================================
# SPLIT HANDLERS
#
# Split flow:
#
# .split
#      ↓
# Reply to release user:
# .r 80
#      ↓
# Reply to refund user:
# .f 120
#      ↓
# SPLIT COMPLETED
#
# Split handlers are registered BEFORE normal
# release/refund and generic handlers.
# ==========================================================

register_split(bot)

register_split_input(bot)


# ==========================================
# START / USER HANDLERS
# ==========================================

register_start_handlers(bot)

register_user_message(bot)

register_admin_reply(bot)


# ==========================================
# LEADERBOARD
# ==========================================

register_leaderboard(bot)

register_user_search(bot)


# ==========================================
# DEAL SYSTEM
# ==========================================

register_deal(bot)

register_removedeal(bot)


# ==========================================
# PAYMENT / MM FEATURES
# ==========================================

register_payment(bot)

register_mm_fee(bot)

register_qr(bot)

register_hold(bot)


# ==========================================
# NORMAL RELEASE / REFUND
#
# These remain separate from Split.
#
# Normal:
# .release
# .refund
#
# Split:
# .r
# .f
# ==========================================

register_release(bot)

register_refund(bot)


# ==========================================
# VOUCHER / FORM
# ==========================================

register_voucher(bot)

register_form(bot)


# ==========================================
# ADMIN PANEL
# ==========================================

register_admin_panel(bot)

start_automatic_backup(bot)


# ==========================================
# CLEAN COMMAND
# ==========================================

register_clean(bot)


# ==========================================
# START BOT
# ==========================================

print(
    "🤖 Rounak MM Bot is starting..."
)


bot.infinity_polling(
    skip_pending=True
)
