from telebot import types
from config import (
    CHANNEL_1,
    CHANNEL_1_LINK,
    CHANNEL_2,
    CHANNEL_2_LINK,
    CHANNEL_3,
    CHANNEL_3_LINK,
    CHANNEL_1_BUTTON,
    CHANNEL_2_BUTTON,
    CHANNEL_3_BUTTON,
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
        "🔐 𝐑𝐎𝐔𝐍𝐀𝐊 𝐌𝐌\n\n"
        "𝐏𝐥𝐞𝐚𝐬𝐞 𝐣𝐨𝐢𝐧 𝐛𝐨𝐭𝐡 𝐜𝐡𝐚𝐧𝐧𝐞𝐥𝐬 𝐛𝐞𝐥𝐨𝐰.\n\n"
        "𝐀𝐟𝐭𝐞𝐫 𝐣𝐨𝐢𝐧𝐢𝐧𝐠, 𝐜𝐥𝐢𝐜𝐤 𝐈'𝐌 𝐃𝐎𝐍𝐄 ✅",
        reply_markup=join_keyboard(),
        parse_mode="Markdown"
    )


def send_main_menu(bot, chat_id):
    bot.send_message(
        chat_id,
        " 🤝 𝘞𝘦𝘭𝘤𝘰𝘮𝘦 𝘵𝘰 𝘙𝘰𝘶𝘯𝘢𝘬 𝘔𝘔\n"
        "𝘗𝘭𝘦𝘢𝘴𝘦 𝘴𝘦𝘭𝘦𝘤𝘵 𝘢𝘯 𝘰𝘱𝘵𝘪𝘰𝘯 𝘣𝘦𝘭𝘰𝘸:",
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
                "ʏᴏᴜ ᴄᴀɴ ɴᴏᴡ ᴜꜱᴇ ʀᴏᴜɴᴀᴋ ᴍᴍ.",
                reply_markup=main_menu_keyboard(),
                parse_mode="Markdown"
            )

        else:

            bot.answer_callback_query(
                call.id,
                "❌ ᴘʟᴇᴀꜱᴇ ᴊᴏɪɴ ʙᴏᴛʜ ᴄʜᴀɴɴᴇʟꜱ ꜰɪʀꜱᴛ.",
                show_alert=True
  )
