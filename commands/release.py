from config import MM_CHAT_IDS, ADMIN_IDS

from database.database import (
    get_active_deal,
    record_release,
    complete_deal
)

from commands.command_utils import (
    normalize_command,
    delete_command_message
)


# ==========================================
# USER MENTION
# ==========================================

def user_mention(user_id, name):

    name = name or "User"

    return (
        f'<a href="tg://user?id={user_id}">'
        f'{name}'
        f'</a>'
    )


# ==========================================
# FIND USER FROM REPLY / MENTION
# ==========================================

def get_target_user(bot, message, active_deal):

    # --------------------------------------
    # REPLY METHOD
    # --------------------------------------

    if message.reply_to_message:

        replied_user = (
            message.reply_to_message.from_user
        )

        if replied_user:

            user_id = replied_user.id

            if user_id in [
                active_deal["user_1_id"],
                active_deal["user_2_id"]
            ]:
                return user_id

    # --------------------------------------
    # MENTION METHOD
    # --------------------------------------

    entities = message.entities or []

    for entity in entities:

        if entity.type == "text_mention":

            user = entity.user

            if user:

                user_id = user.id

                if user_id in [
                    active_deal["user_1_id"],
                    active_deal["user_2_id"]
                ]:
                    return user_id

        elif entity.type == "mention":

            text = message.text or ""

            username = text[
                entity.offset:
                entity.offset + entity.length
            ].lstrip("@").lower()

            for user_id in [
                active_deal["user_1_id"],
                active_deal["user_2_id"]
            ]:

                try:

                    chat = bot.get_chat(user_id)

                    chat_username = (
                        chat.username or ""
                    ).lower()

                    if (
                        chat_username
                        and chat_username == username
                    ):
                        return user_id

                except Exception as error:

                    print(
                        f"Release username lookup error: {error}"
                    )

    return None


# ==========================================
# REGISTER RELEASE
# ==========================================

def register_release(bot):

    @bot.message_handler(
        func=lambda message:
        message.text
        and normalize_command(message.text)
        .lower()
        .startswith(".release")
    )
    def release_command(message):

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
            return

        # ==================================
        # ACTIVE DEAL
        # ==================================

        active_deal = get_active_deal(
            message.chat.id
        )

        if not active_deal:

            bot.reply_to(
                message,
                "⚠️ Is group mein koi active deal nahi hai."
            )

            delete_command_message(
                bot,
                message
            )

            return

        # ==================================
        # CHECK HOLD
        # ==================================

        holding_amount = float(
            active_deal["holding_amount"] or 0
        )

        if holding_amount <= 0:

            bot.reply_to(
                message,
                "⚠️ Pehle payment ko hold karo."
            )

            delete_command_message(
                bot,
                message
            )

            return

        # ==================================
        # COMMAND
        # ==================================

        normalized_text = normalize_command(
            message.text
        )

        parts = normalized_text.strip().split()

        # ==================================
        # USER CHECK
        # ==================================

        target_user_id = get_target_user(
            bot,
            message,
            active_deal
        )

        if not target_user_id:

            bot.reply_to(
                message,
                (
                    "⚠️ Release kis user ko karna hai?\n\n"
                    "User ko mention karo ya uske message par "
                    "reply karke use karo.\n\n"
                    "<code>.release @username</code>"
                ),
                parse_mode="HTML"
            )

            delete_command_message(
                bot,
                message
            )

            return

        # ==================================
        # GET USER NAME
        # ==================================

        try:

            target_user = bot.get_chat(
                target_user_id
            )

            target_name = (
                target_user.first_name
                or "User"
            )

        except Exception as error:

            print(
                f"Release user lookup error: {error}"
            )

            target_name = "User"

        mention = user_mention(
            target_user_id,
            target_name
        )

        # ==================================
        # RELEASE
        # ==================================

        success = record_release(
            active_deal["deal_id"],
            target_user_id,
            holding_amount
        )

        if not success:

            bot.reply_to(
                message,
                "❌ Release process failed."
            )

            delete_command_message(
                bot,
                message
            )

            return

        # ==================================
        # COMPLETE DEAL
        # ==================================

        completed = complete_deal(
            active_deal["deal_id"]
        )

        if not completed:

            bot.reply_to(
                message,
                "⚠️ Release save ho gaya, lekin deal complete nahi ho payi."
            )

            delete_command_message(
                bot,
                message
            )

            return

        # ==================================
        # FORMAT AMOUNT
        # ==================================

        amount_text = f"₹{holding_amount:g}"

        # ==================================
        # RELEASE MESSAGE
        # ==================================

        bot.send_message(
            message.chat.id,
            (
                f"✅ <b>PAYMENT RELEASED — {amount_text}</b>\n\n"

                f"💰 <b>{amount_text} RELEASED</b>\n"
                f"👤 <b>Receiver:</b> {mention}\n\n"

                "🎉 <b>Deal completed successfully.</b>\n"
                "📌 This deal is now closed."
            ),
            parse_mode="HTML"
        )

        # ==================================
        # DELETE COMMAND
        # ==================================

        delete_command_message(
            bot,
            message
        )
