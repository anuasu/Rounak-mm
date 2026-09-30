from config import MM_CHAT_IDS, ADMIN_IDS

from database.database import (
    save_user,
    create_deal,
    get_active_deal
)

# ==========================================
# TEMPORARY DEAL SETUP
# group_chat_id -> first user
# ==========================================

pending_deal_users = {}


# ==========================================
# GET USER FROM REPLY
# ==========================================

def get_replied_user(message):

    if not message.reply_to_message:
        return None

    user = message.reply_to_message.from_user

    if not user:
        return None

    if user.is_bot:
        return None

    return user


# ==========================================
# REGISTER DEAL
# ==========================================

def register_deal(bot):

    # ======================================
    # .deal
    # ======================================

    @bot.message_handler(
        func=lambda message:
        message.text
        and message.text.strip().lower() == ".deal"
    )
    def deal_command(message):

        # ----------------------------------
        # MM ONLY
        # ----------------------------------

        if message.from_user.id not in MM_CHAT_IDS:

            if message.from_user.id in ADMIN_IDS:
                bot.reply_to(
                    message,
                    "⚠️ Sirf MM ye command use kar sakta hai."
                )

            return

        # ----------------------------------
        # GROUP ONLY
        # ----------------------------------

        if message.chat.type not in [
            "group",
            "supergroup"
        ]:
            bot.reply_to(
                message,
                "❌ .deal sirf group mein use kar sakte ho."
            )
            return

        group_id = message.chat.id

        # ----------------------------------
        # GET REPLIED USER
        # ----------------------------------

        user = get_replied_user(message)

        if not user:

            bot.reply_to(
                message,
                (
                    "⚠️ Kisi user ke message ko "
                    "reply karke <code>.deal</code> bhejo."
                ),
                parse_mode="HTML"
            )
            return

        # ----------------------------------
        # CHECK ALREADY COMPLETED/ACTIVE DEAL
        # ----------------------------------

        active_deal = get_active_deal(group_id)

        if active_deal:

            bot.reply_to(
                message,
                (
                    f"⚠️ Is group mein already "
                    f"<b>Deal #{active_deal['deal_id']}</b> active hai.\n\n"
                    "Pehle <code>.removedeal</code> ya "
                    "deal completion process use karo."
                ),
                parse_mode="HTML"
            )
            return

        # ----------------------------------
        # FIRST USER
        # ----------------------------------

        if group_id not in pending_deal_users:

            pending_deal_users[group_id] = {
                "user_1_id": user.id,
                "user_1_name": user.first_name or "Unknown",
                "user_1_username": user.username or ""
            }

            save_user(
                chat_id=user.id,
                first_name=user.first_name or "",
                username=user.username or ""
            )

            username = (
                f"@{user.username}"
                if user.username
                else "No Username"
            )

            bot.reply_to(
                message,
                (
                    "🤝 <b>DEAL SETUP</b>\n\n"

                    "👤 <b>User 1:</b>\n"
                    f"Name: {user.first_name or 'Unknown'}\n"
                    f"Username: {username}\n"
                    f"🆔 <code>{user.id}</code>\n\n"

                    "⏳ <b>Waiting for User 2...</b>\n\n"

                    "➡️ Dusre user ke message ko reply "
                    "karke <code>.deal</code> bhejo.\n\n"

                    "🗑️ Galat user ho to:\n"
                    "<code>.removedeal</code>"
                ),
                parse_mode="HTML"
            )

            return

        # ----------------------------------
        # SECOND USER
        # ----------------------------------

        deal_data = pending_deal_users[group_id]

        user_1_id = deal_data["user_1_id"]
        user_2_id = user.id

        # ----------------------------------
        # SAME USER CHECK
        # ----------------------------------

        if user_1_id == user_2_id:

            bot.reply_to(
                message,
                "⚠️ User 1 aur User 2 same nahi ho sakte."
            )
            return

        # ----------------------------------
        # SAVE USER 2
        # ----------------------------------

        save_user(
            chat_id=user.id,
            first_name=user.first_name or "",
            username=user.username or ""
        )

        # ----------------------------------
        # CREATE DEAL
        # ----------------------------------

        deal_id = create_deal(
            group_chat_id=group_id,
            user_1_id=user_1_id,
            user_2_id=user_2_id
        )

        # ----------------------------------
        # USER DETAILS
        # ----------------------------------

        user_1_username = (
            f"@{deal_data['user_1_username']}"
            if deal_data["user_1_username"]
            else "No Username"
        )

        user_2_username = (
            f"@{user.username}"
            if user.username
            else "No Username"
        )

        # ----------------------------------
        # CLEAR TEMP SETUP
        # ----------------------------------

        pending_deal_users.pop(
            group_id,
            None
        )

        # ----------------------------------
        # FINAL DEAL MESSAGE
        # ----------------------------------

        bot.send_message(
            group_id,
            (
                "🤝 <b>DEAL ADDED</b>\n\n"

                f"👤 <b>User 1:</b> "
                f"{deal_data['user_1_name']}\n"
                f"🔗 {user_1_username}\n"
                f"🆔 <code>{user_1_id}</code>\n\n"

                f"👤 <b>User 2:</b> "
                f"{user.first_name or 'Unknown'}\n"
                f"🔗 {user_2_username}\n"
                f"🆔 <code>{user_2_id}</code>\n\n"

                "━━━━━━━━━━━━━━━━━━\n\n"

                f"🤝 <b>Deal ID:</b> #{deal_id}\n"
                f"💬 <b>Group ID:</b> <code>{group_id}</code>\n"
                "⏳ <b>Status:</b> Active\n\n"

                "💰 Ab amount ke liye "
                "<code>.payment</code> use karo."
            ),
            parse_mode="HTML"
        )

