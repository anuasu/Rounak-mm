from telebot import types

from config import ADMIN_IDS


# ==========================================
# USERS JO ADMIN KO MESSAGE KAR RAHE HAIN
# ==========================================

waiting_for_message = set()


# ==========================================
# MESSAGE TO MM BUTTON
# ==========================================

def register_user_message(bot):

    @bot.callback_query_handler(
        func=lambda call: call.data == "message_to_mm"
    )
    def message_to_mm(call):

        user_id = call.from_user.id

        waiting_for_message.add(user_id)

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            "💬 *Message to MM*\n\n"
            "Apna message bhejo.\n"
            "Aap koi bhi custom message bhej sakte ho.",
            parse_mode="Markdown"
        )


    # ==========================================
    # USER MESSAGE RECEIVE
    # ==========================================

    @bot.message_handler(
        func=lambda message:
        message.from_user.id in waiting_for_message
    )
    def receive_user_message(message):

        user_id = message.from_user.id

        waiting_for_message.discard(user_id)

        first_name = message.from_user.first_name or "Unknown"

        username = (
            f"@{message.from_user.username}"
            if message.from_user.username
            else "No Username"
        )

        chat_id = message.from_user.id


        # ==========================================
        # ADMIN MESSAGE
        # ==========================================

        admin_text = (
            "📩 *NEW MESSAGE TO MM*\n\n"

            f"👤 Name: *{first_name}*\n"
            f"🔗 Username: {username}\n"
            f"🆔 Chat ID: `{chat_id}`\n\n"

            "💬 *Message:*\n"
            f"{message.text or '[Non-text message]'}"
        )


        # ==========================================
        # REPLY BUTTON
        # ==========================================

        keyboard = types.InlineKeyboardMarkup()

        keyboard.add(
            types.InlineKeyboardButton(
                "↩️ Reply to User",
                callback_data=f"reply_user:{chat_id}"
            )
        )


        # ==========================================
        # SEND TO ALL ADMINS
        # ==========================================

        for admin_id in ADMIN_IDS:

            try:

                bot.send_message(
                    admin_id,
                    admin_text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )

            except Exception as error:

                print(
                    f"Admin {admin_id} ko message nahi gaya: {error}"
                )


        # ==========================================
        # USER CONFIRMATION
        # ==========================================

        bot.send_message(
            message.chat.id,
            "✅ *Message MM ko send ho gaya.*\n\n"
            "MM aapko yahin reply karega.",
            parse_mode="Markdown"
      )
