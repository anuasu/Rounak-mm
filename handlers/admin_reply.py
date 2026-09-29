from telebot import types

from config import ADMIN_IDS


# ==========================================
# ADMIN REPLY SYSTEM
# ==========================================

def register_admin_reply(bot):

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith("reply_user:")
    )
    def reply_to_user(call):

        # ======================================
        # ADMIN CHECK
        # ======================================

        if call.from_user.id not in ADMIN_IDS:

            bot.answer_callback_query(
                call.id,
                "❌ Sirf admin is option ko use kar sakta hai.",
                show_alert=True
            )

            return

        # ======================================
        # USER CHAT ID
        # ======================================

        try:
            user_id = int(
                call.data.split(":", 1)[1]
            )

        except (ValueError, IndexError):

            bot.answer_callback_query(
                call.id,
                "❌ Invalid user ID.",
                show_alert=True
            )

            return

        bot.answer_callback_query(call.id)

        # ======================================
        # ASK ADMIN FOR REPLY
        # ======================================

        msg = bot.send_message(
            call.message.chat.id,
            "✍️ *Reply to User*\n\n"
            "Ab jo message user ko bhejna hai, "
            "wo send karo.",
            parse_mode="Markdown"
        )

        # Next message admin ka reply hoga
        bot.register_next_step_handler(
            msg,
            lambda message: send_reply_to_user(
                bot,
                message,
                user_id
            )
        )


# ==========================================
# SEND ADMIN REPLY TO USER
# ==========================================

def send_reply_to_user(bot, message, user_id):

    # ======================================
    # ADMIN CHECK
    # ======================================

    if message.from_user.id not in ADMIN_IDS:

        bot.send_message(
            message.chat.id,
            "❌ Sirf admin user ko reply kar sakta hai."
        )

        return

    try:

        # ==================================
        # COPY ADMIN MESSAGE TO USER
        # ==================================

        bot.copy_message(
            chat_id=user_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )

        # ==================================
        # ADMIN CONFIRMATION
        # ==================================

        bot.send_message(
            message.chat.id,
            "✅ *Reply user ko successfully send ho gaya.*",
            parse_mode="Markdown"
        )

    except Exception as error:

        print(f"Reply error: {error}")

        bot.send_message(
            message.chat.id,
            "❌ User ko reply send nahi ho paya."
      )
