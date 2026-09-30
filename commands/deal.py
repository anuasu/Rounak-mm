from config import MM_CHAT_IDS, ADMIN_IDS

from database.database import (
    save_user,
    create_deal,
    get_active_deal
)


# ==========================================
# EXTRACT USERS FROM MESSAGE
# ==========================================

def extract_users_from_message(message, bot):

    users = []

    if not message.entities:
        return users

    for entity in message.entities:

        # ----------------------------------
        # TELEGRAM TEXT MENTION
        # ----------------------------------

        if entity.type == "text_mention":

            user = entity.user

            if user and not user.is_bot:
                users.append(user)

        # ----------------------------------
        # @USERNAME MENTION
        # ----------------------------------

        elif entity.type == "mention":

            try:

                username = message.text[
                    entity.offset + 1:
                    entity.offset + entity.length
                ]

                chat = bot.get_chat(
                    "@" + username
                )

                if chat.type == "private":

                    users.append(chat)

            except Exception as error:

                print(
                    f"Username lookup error: {error}"
                )

    # --------------------------------------
    # REMOVE DUPLICATE USERS
    # --------------------------------------

    unique_users = []
    seen_ids = set()

    for user in users:

        if user.id not in seen_ids:

            seen_ids.add(user.id)
            unique_users.append(user)

    return unique_users


# ==========================================
# REGISTER DEAL
# ==========================================

def register_deal(bot):

    @bot.message_handler(
        func=lambda message:
        message.text
        and message.text.lower().startswith(".deal")
    )
    def deal_command(message):

        # ==================================
        # MM / ADMIN PERMISSION
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
        # EXTRACT TWO USERS
        # ==================================

        users = extract_users_from_message(
            message,
            bot
        )

        # ==================================
        # CHECK USERS
        # ==================================

        if len(users) < 2:

            bot.reply_to(
                message,
                (
                    "⚠️ <b>2 users mention karo.</b>\n\n"

                    "Example:\n"
                    "<code>.deal @username1 @username2</code>\n\n"

                    "Agar username nahi hai, "
                    "Telegram ka mention/select option "
                    "use karo."
                ),
                parse_mode="HTML"
            )

            return

        # ----------------------------------
        # ONLY FIRST TWO USERS
        # ----------------------------------

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
        # CREATE DEAL
        # ==================================

        deal_id = create_deal(
            group_chat_id=message.chat.id,
            user_1_id=user_1.id,
            user_2_id=user_2.id
        )

        # ==================================
        # USER 1 DETAILS
        # ==================================

        user_1_name = (
            user_1.first_name
            or "Unknown"
        )

        if user_1.username:

            user_1_username = (
                f"@{user_1.username}"
            )

        else:

            user_1_username = (
                "No Username"
            )

        # ==================================
        # USER 2 DETAILS
        # ==================================

        user_2_name = (
            user_2.first_name
            or "Unknown"
        )

        if user_2.username:

            user_2_username = (
                f"@{user_2.username}"
            )

        else:

            user_2_username = (
                "No Username"
            )

        # ==================================
        # DEAL MESSAGE
        # ==================================

        text = (

            "🤝 <b>DEAL ADDED</b>\n\n"

            f"👤 <b>User 1:</b> "
            f"{user_1_name}\n"

            f"🔗 {user_1_username}\n"

            f"🆔 <code>{user_1.id}</code>\n\n"

            f"👤 <b>User 2:</b> "
            f"{user_2_name}\n"

            f"🔗 {user_2_username}\n"

            f"🆔 <code>{user_2.id}</code>\n\n"

            "━━━━━━━━━━━━━━━━━━\n\n"

            f"🤝 <b>Deal ID:</b> #{deal_id}\n"

            f"💬 <b>Group ID:</b> "
            f"<code>{message.chat.id}</code>\n"

            "⏳ <b>Status:</b> Active"
        )

        # ==================================
        # SEND DEAL MESSAGE
        # ==================================

        bot.send_message(
            message.chat.id,
            text,
            parse_mode="HTML"
        )
