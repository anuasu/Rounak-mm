from config import MM_CHAT_IDS, ADMIN_IDS

from database.database import (
    save_user,
    create_deal,
    get_active_deal
)


# ==========================================
# TEMPORARY DEAL USERS
# ==========================================

pending_deal_users = {}


# ==========================================
# REGISTER DEAL
# ==========================================

def register_deal(bot):

    @bot.message_handler(
        func=lambda message:
        message.text
        and message.text.lower().strip() == ".deal"
    )
    def deal_command(message):

        # ==================================
        # MM ONLY
        # ==================================

        if message.from_user.id not in MM_CHAT_IDS:

            if message.from_user.id in ADMIN_IDS:

                bot.reply_to(
                    message,
                    "⚠️ Sirf MM ye command use kar sakta hai."
                )

            return

        # ==================================
        # GROUP ONLY
        # ==================================

        if message.chat.type not in [
            "group",
            "supergroup"
        ]:

            bot.reply_to(
                message,
                "❌ .deal sirf group mein use kar sakte ho."
            )

            return

        # ==================================
        # MUST REPLY TO USER MESSAGE
        # ==================================

        if not message.reply_to_message:

            bot.reply_to(
                message,
                (
                    "⚠️ Kisi user ke message ko "
                    "reply karke <code>.deal</code> bhejo."
                ),
                parse_mode="HTML"
            )

            return

        replied_user = (
            message.reply_to_message.from_user
        )

        # ==================================
        # BOT CHECK
        # ==================================

        if not replied_user:

            bot.reply_to(
                message,
                "❌ User identify nahi ho paya."
            )

            return

        if replied_user.is_bot:

            bot.reply_to(
                message,
                "❌ Bot ko deal mein add nahi kar sakte."
            )

            return

        # ==================================
        # CHECK EXISTING ACTIVE DEAL
        # ==================================

        existing_deal = get_active_deal(
            message.chat.id
        )

        # ==================================
        # FIRST USER
        # ==================================

        if not existing_deal:

            pending_deal_users[
                message.chat.id
            ] = replied_user.id

            # Save user immediately

            save_user(
                chat_id=replied_user.id,
                first_name=replied_user.first_name or "",
                username=replied_user.username or ""
            )

            username_text = (
                f"@{replied_user.username}"
                if replied_user.username
                else "No Username"
            )

            bot.reply_to(
                message,
                (
                    "✅ <b>User 1 added</b>\n\n"

                    f"👤 <b>Name:</b> "
                    f"{replied_user.first_name or 'Unknown'}\n"

                    f"🔗 <b>Username:</b> "
                    f"{username_text}\n"

                    f"🆔 <b>Chat ID:</b> "
                    f"<code>{replied_user.id}</code>\n\n"

                    "➡️ Ab <b>dusre user</b> ke message ko "
                    "reply karke dobara:\n"
                    "<code>.deal</code>\n\n"

                    "likho."
                ),
                parse_mode="HTML"
            )

            return

        # ==================================
        # SECOND USER
        # ==================================

        user_1_id = pending_deal_users.get(
            message.chat.id
        )

        if not user_1_id:

            bot.reply_to(
                message,
                "⚠️ Pehle User 1 select karo."
            )

            return

        user_2_id = replied_user.id

        # ==================================
        # SAME USER CHECK
        # ==================================

        if user_1_id == user_2_id:

            bot.reply_to(
                message,
                "⚠️ Same user ko dono side add nahi kar sakte."
            )

            return

        # ==================================
        # SAVE USER 2
        # ==================================

        save_user(
            chat_id=replied_user.id,
            first_name=replied_user.first_name or "",
            username=replied_user.username or ""
        )

        # ==================================
        # CREATE DEAL
        # ==================================

        deal_id = create_deal(
            group_chat_id=message.chat.id,
            user_1_id=user_1_id,
            user_2_id=user_2_id
        )

        # ==================================
        # GET USER 1 DETAILS
        # ==================================

        try:

            user_1 = bot.get_chat(user_1_id)

        except Exception:

            user_1 = None

        # ==================================
        # USER 1 DISPLAY
        # ==================================

        if user_1:

            user_1_name = (
                user_1.first_name
                or "Unknown"
            )

            user_1_username = (
                f"@{user_1.username}"
                if user_1.username
                else "No Username"
            )

        else:

            user_1_name = "Unknown"
            user_1_username = "No Username"

        # ==================================
        # USER 2 DISPLAY
        # ==================================

        user_2_name = (
            replied_user.first_name
            or "Unknown"
        )

        user_2_username = (
            f"@{replied_user.username}"
            if replied_user.username
            else "No Username"
        )

        # ==================================
        # REMOVE TEMP DATA
        # ==================================

        pending_deal_users.pop(
            message.chat.id,
            None
        )

        # ==================================
        # DEAL CREATED MESSAGE
        # ==================================

        text = (
            "🤝 <b>DEAL ADDED</b>\n\n"

            f"👤 <b>User 1:</b> "
            f"{user_1_name}\n"
            f"🔗 {user_1_username}\n"
            f"🆔 <code>{user_1_id}</code>\n\n"

            f"👤 <b>User 2:</b> "
            f"{user_2_name}\n"
            f"🔗 {user_2_username}\n"
            f"🆔 <code>{user_2_id}</code>\n\n"

            "━━━━━━━━━━━━━━━━━━\n\n"

            f"🤝 <b>Deal ID:</b> #{deal_id}\n"
            f"💬 <b>Group ID:</b> "
            f"<code>{message.chat.id}</code>\n"
            "⏳ <b>Status:</b> Active"
        )

        bot.send_message(
            message.chat.id,
            text,
            parse_mode="HTML"
        )
