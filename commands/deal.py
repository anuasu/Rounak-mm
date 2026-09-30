from config import MM_CHAT_IDS, ADMIN_IDS

from database.database import (
    save_user,
    create_deal,
    get_active_deal
)


# ==========================================
# GET 2 USERS FROM TELEGRAM MENTIONS
# ==========================================

def get_mentioned_users(message):

    users = []

    if not message.entities:
        return users

    for entity in message.entities:

        # Telegram's real user mention
        if entity.type == "text_mention":

            user = entity.user

            if user and not user.is_bot:
                users.append(user)

    # Remove duplicate users
    unique_users = []
    seen_ids = set()

    for user in users:

        if user.id not in seen_ids:

            seen_ids.add(user.id)
            unique_users.append(user)

    return unique_users


# ==========================================
# REGISTER DEAL COMMAND
# ==========================================

def register_deal(bot):

    @bot.message_handler(
        func=lambda message:
        message.text
        and message.text.lower().startswith(".deal")
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
        # CHECK ACTIVE DEAL
        # ==================================

        existing_deal = get_active_deal(
            message.chat.id
        )

        if existing_deal:

            bot.reply_to(
                message,
                (
                    "⚠️ Is group mein already "
                    f"<b>Deal #{existing_deal['deal_id']}</b> "
                    "active hai.\n\n"
                    "Pehle current deal complete karo."
                ),
                parse_mode="HTML"
            )

            return

        # ==================================
        # GET MENTIONED USERS
        # ==================================

        users = get_mentioned_users(message)

        # ==================================
        # EXACTLY 2 USERS
        # ==================================

        if len(users) != 2:

            bot.reply_to(
                message,
                (
                    "⚠️ <b>2 users ko Telegram mention "
                    "ke through select karo.</b>\n\n"

                    "Example:\n"
                    "<code>.deal @User1 @User2</code>\n\n"

                    "Username ko sirf text ki tarah type "
                    "mat karo. Telegram ka user mention "
                    "select karo."
                ),
                parse_mode="HTML"
            )

            return

        # ==================================
        # USER DATA
        # ==================================

        user_1 = users[0]
        user_2 = users[1]

        # ==================================
        # SAVE USER 1
        # ==================================

        save_user(
            chat_id=user_1.id,
            first_name=user_1.first_name or "",
            username=user_1.username or ""
        )

        # ==================================
        # SAVE USER 2
        # ==================================

        save_user(
            chat_id=user_2.id,
            first_name=user_2.first_name or "",
            username=user_2.username or ""
        )

        # ==================================
        # CREATE ACTIVE DEAL
        # ==================================

        deal_id = create_deal(
            group_chat_id=message.chat.id,
            user_1_id=user_1.id,
            user_2_id=user_2.id
        )

        # ==================================
        # USER 1 DISPLAY
        # ==================================

        user_1_name = (
            user_1.first_name
            or "Unknown"
        )

        user_1_username = (
            f"@{user_1.username}"
            if user_1.username
            else "No Username"
        )

        # ==================================
        # USER 2 DISPLAY
        # ==================================

        user_2_name = (
            user_2.first_name
            or "Unknown"
        )

        user_2_username = (
            f"@{user_2.username}"
            if user_2.username
            else "No Username"
        )

        # ==================================
        # DEAL CREATED MESSAGE
        # ==================================

        text = (
            "🤝 <b>DEAL ADDED</b>\n\n"

            f"👤 <b>User 1:</b> {user_1_name}\n"
            f"🔗 {user_1_username}\n"
            f"🆔 <code>{user_1.id}</code>\n\n"

            f"👤 <b>User 2:</b> {user_2_name}\n"
            f"🔗 {user_2_username}\n"
            f"🆔 <code>{user_2.id}</code>\n\n"

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
