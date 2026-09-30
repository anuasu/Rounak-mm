from telebot import types

from database.database import (
    save_user,
    create_deal
)


# ==========================================
# ACTIVE DEALS
# ==========================================

active_deals = {}


# ==========================================
# DEAL COMMAND
# ==========================================

def register_deal(bot):

    @bot.message_handler(commands=["deal"])
    def deal_command(message):

        # ----------------------------------
        # Group only
        # ----------------------------------

        if message.chat.type not in ["group", "supergroup"]:
            bot.reply_to(
                message,
                "❌ .deal sirf group mein use kar sakte ho."
            )
            return

        # ----------------------------------
        # Reply based user selection
        # ----------------------------------

        if not message.reply_to_message:
            bot.reply_to(
                message,
                "⚠️ Pehle ek user ke message ko reply karo.\n\n"
                "Example:\n"
                ".deal"
            )
            return

        user_1 = message.reply_to_message.from_user
        user_2 = message.from_user

        # ----------------------------------
        # Bot protection
        # ----------------------------------

        if user_1.is_bot or user_2.is_bot:
            bot.reply_to(
                message,
                "❌ Bot ko deal user ke roop mein add nahi kar sakte."
            )
            return

        # ----------------------------------
        # Same user protection
        # ----------------------------------

        if user_1.id == user_2.id:
            bot.reply_to(
                message,
                "❌ Deal ke liye 2 different users chahiye."
            )
            return

        # ----------------------------------
        # Save users
        # ----------------------------------

        save_user(
            chat_id=user_1.id,
            first_name=user_1.first_name or "",
            username=user_1.username or ""
        )

        save_user(
            chat_id=user_2.id,
            first_name=user_2.first_name or "",
            username=user_2.username or ""
        )

        # ----------------------------------
        # Create pending deal
        # ----------------------------------

        deal_id = create_deal(
            user_1_id=user_1.id,
            user_2_id=user_2.id
        )

        # ----------------------------------
        # Store active deal for group
        # ----------------------------------

        active_deals[message.chat.id] = {
            "deal_id": deal_id,
            "user_1_id": user_1.id,
            "user_2_id": user_2.id
        }

        # ----------------------------------
        # Display names
        # ----------------------------------

        user_1_name = user_1.first_name or "Unknown"
        user_2_name = user_2.first_name or "Unknown"

        # ----------------------------------
        # Deal created message
        # ----------------------------------

        text = (
            "🤝 <b>DEAL ADDED</b>\n\n"
            f"👤 User 1: <b>{user_1_name}</b>\n"
            f"🆔 <code>{user_1.id}</code>\n\n"
            f"👤 User 2: <b>{user_2_name}</b>\n"
            f"🆔 <code>{user_2.id}</code>\n\n"
            f"🆔 Deal ID: <code>#{deal_id}</code>\n\n"
            "⏳ Status: <b>Pending</b>"
        )

        keyboard = types.InlineKeyboardMarkup()

        keyboard.add(
            types.InlineKeyboardButton(
                "📋 Deal Added",
                callback_data=f"deal_info:{deal_id}"
            )
        )

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )


# ==========================================
# DEAL INFO BUTTON
# ==========================================

def register_deal_info(bot):

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith("deal_info:")
    )
    def deal_info(call):

        bot.answer_callback_query(call.id)

        try:
            deal_id = int(
                call.data.split(":", 1)[1]
            )
        except (ValueError, IndexError):
            return

        deal = None

        for chat_id, data in active_deals.items():

            if data["deal_id"] == deal_id:
                deal = data
                break

        if not deal:
            bot.answer_callback_query(
                call.id,
                "❌ Deal active nahi hai.",
                show_alert=True
            )
            return

        text = (
            "🤝 <b>CURRENT DEAL</b>\n\n"
            f"🆔 Deal ID: <code>#{deal_id}</code>\n\n"
            f"👤 User 1 ID: <code>{deal['user_1_id']}</code>\n"
            f"👤 User 2 ID: <code>{deal['user_2_id']}</code>\n\n"
            "⏳ Status: <b>Pending</b>"
        )

        bot.send_message(
            call.message.chat.id,
            text,
            parse_mode="HTML"
          )
