from telebot import types
from config import (
    CHANNEL_1,
    CHANNEL_1_LINK,
    CHANNEL_2,
    CHANNEL_2_LINK,
    CHANNEL_1_BUTTON,
    CHANNEL_2_BUTTON,
    CHECK_JOIN_BUTTON,
)


def join_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        types.InlineKeyboardButton(
            CHANNEL_1_BUTTON,
            url=CHANNEL_1_LINK
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            CHANNEL_2_BUTTON,
            url=CHANNEL_2_LINK
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            CHECK_JOIN_BUTTON,
            callback_data="check_join"
        )
    )

    return keyboard


def main_menu_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        types.InlineKeyboardButton(
            "💬 Message to MM",
            callback_data="message_to_mm"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "🏆 Leaderboard",
            callback_data="leaderboard"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "💰 What MM Fee?",
            callback_data="mm_fee"
        )
    )

    return keyboard


def is_user_joined(bot, user_id):
    channels = [CHANNEL_1, CHANNEL_2]

    for channel in channels:
        try:
            member = bot.get_chat_member(channel, user_id)

            if member.status in ["left", "kicked"]:
                return False

        except Exception:
            return False

    return True


def send_join_message(bot, chat_id):
    bot.send_message(
        chat_id,
        "🔐 *Raunak MM*\n\n"
        "Bot use karne ke liye pehle dono required "
        "channels join karo.\n\n"
        "Join karne ke baad *✅ Check Join* par click karo.",
        reply_markup=join_keyboard(),
        parse_mode="Markdown"
    )


def send_main_menu(bot, chat_id):
    bot.send_message(
        chat_id,
        "🤝 *Welcome to Raunak MM*\n\n"
        "Neeche se option select karo:",
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )


def register_start_handlers(bot):

    @bot.message_handler(commands=["start"])
    def start_command(message):

        if is_user_joined(bot, message.from_user.id):
            send_main_menu(bot, message.chat.id)
        else:
            send_join_message(bot, message.chat.id)

    @bot.callback_query_handler(func=lambda call: call.data == "check_join")
    def check_join(call):

        if is_user_joined(bot, call.from_user.id):

            bot.answer_callback_query(
                call.id,
                "✅ Verification successful!"
            )

            bot.send_message(
                call.message.chat.id,
                "✅ *Verification successful!*\n\n"
                "Ab aap Raunak MM use kar sakte ho.",
                reply_markup=main_menu_keyboard(),
                parse_mode="Markdown"
            )

        else:

            bot.answer_callback_query(
                call.id,
                "❌ Pehle dono channels join karo.",
                show_alert=True
  )
