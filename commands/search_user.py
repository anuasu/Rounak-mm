from database.database import search_user


# ==========================================
# SEARCH USER SYSTEM
# ==========================================

def register_user_search(bot):

    waiting_for_user_id = set()

    # ======================================
    # SEARCH BUTTON
    # ======================================

    @bot.callback_query_handler(
        func=lambda call: call.data == "search_user"
    )
    def search_user_button(call):

        bot.answer_callback_query(call.id)

        waiting_for_user_id.add(call.from_user.id)

        bot.send_message(
            call.message.chat.id,
            "🔎 <b>Search User ID</b>\n\n"
            "User ka Telegram Chat ID send karo.",
            parse_mode="HTML"
        )

    # ======================================
    # RECEIVE CHAT ID
    # ======================================

    @bot.message_handler(
        func=lambda message:
        message.from_user.id in waiting_for_user_id
    )
    def receive_user_id(message):

        user_id = message.from_user.id

        waiting_for_user_id.discard(user_id)

        # ----------------------------------
        # Check number
        # ----------------------------------

        try:
            searched_id = int(message.text.strip())

        except (ValueError, AttributeError):

            bot.send_message(
                message.chat.id,
                "❌ Valid Chat ID send karo."
            )

            return

        # ----------------------------------
        # Database search
        # ----------------------------------

        user = search_user(searched_id)

        # ----------------------------------
        # No data
        # ----------------------------------

        if not user:

            bot.send_message(
                message.chat.id,
                "❌ <b>No data found</b>\n\n"
                f"🆔 Chat ID: <code>{searched_id}</code>\n"
                "🤝 Deals: <b>0</b>",
                parse_mode="HTML"
            )

            return

        # ----------------------------------
        # User information
        # ----------------------------------

        name = user["first_name"] or "Unknown"

        username = (
            f"@{user['username']}"
            if user["username"]
            else "No Username"
        )

        deals = user["completed_deals"]
        amount = user["total_deal_amount"]

        # ----------------------------------
        # Result
        # ----------------------------------

        text = (
            "🔎 <b>USER INFORMATION</b>\n\n"

            f"👤 Name: <b>{name}</b>\n"
            f"🔗 Username: {username}\n"
            f"🆔 Chat ID: <code>{searched_id}</code>\n\n"

            f"🤝 Completed Deals: <b>{deals}</b>\n"
            f"💰 Total Deal Amount: <b>₹{amount:g}</b>"
        )

        bot.send_message(
            message.chat.id,
            text,
            parse_mode="HTML"
        )
