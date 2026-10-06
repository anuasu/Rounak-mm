from config import MM_CHAT_IDS, ADMIN_IDS

from database.database import (
    get_active_deal,
    record_refund,
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
# REGISTER REFUND
# ==========================================

def register_refund(bot):

    @bot.message_handler(
        func=lambda message:
        message.text
        and normalize_command(message.text)
        .lower()
        .startswith(".refund")
    )
    def refund_command(message):

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
        # GET ACTIVE DEAL
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
        # NORMALIZE COMMAND
        # ==================================

        normalized_text = normalize_command(
            message.text
        )

        parts = normalized_text.strip().split()

        # ==================================
        # USER CHECK
        # ==================================

        if len(parts) != 2:

            bot.reply_to(
                message,
                (
                    "⚠️ Refund kis user ko karna hai?\n\n"
                    "Example:\n"
                    "<code>.refund @username</code>"
                ),
                parse_mode="HTML"
            )

            delete_command_message(
                bot,
                message
            )

            return

        # ==================================
        # FIND REPLY / MENTION USER
        # ==================================

        target_user = None

        # Reply method
        if message.reply_to_message:

            target_user = (
                message.reply_to_message
                .from_user
            )

        # Mention / username method
        if target_user is None:

            username_text = parts[1].lstrip("@").lower()

            try:

                members = []

                user_1 = bot.get_chat(
                    active_deal["user_1_id"]
                )

                user_2 = bot.get_chat(
                    active_deal["user_2_id"]
                )

                members = [
                    user_1,
                    user_2
                ]

                for user in members:

                    if (
                        user.username
                        and user.username.lower()
                        == username_text
                    ):

                        target_user = user
                        break

            except Exception as error:

                print(
                    f"Refund user lookup error: {error}"
                )

        # ==================================
        # USER NOT FOUND
        # ==================================

        if target_user is None:

            bot.reply_to(
                message,
                "⚠️ User active deal mein nahi mila."
            )

            delete_command_message(
                bot,
                message
            )

            return

        target_user_id = target_user.id

        # ==================================
        # CHECK DEAL USER
        # ==================================

        if target_user_id not in [
            active_deal["user_1_id"],
            active_deal["user_2_id"]
        ]:

            bot.reply_to(
                message,
                "⚠️ Ye user is active deal ka part nahi hai."
            )

            delete_command_message(
                bot,
                message
            )

            return

        # ==================================
        # HOLD CHECK
        # ==================================

        holding_amount = (
            active_deal["holding_amount"]
            or 0
        )

        if holding_amount <= 0:

            bot.reply_to(
                message,
                "⚠️ Is deal mein koi holding amount nahi hai."
            )

            delete_command_message(
                bot,
                message
            )

            return

        # ==================================
        # REFUND
        # ==================================

        success = record_refund(
            active_deal["deal_id"],
            target_user_id,
            holding_amount
        )

        if not success:

            bot.reply_to(
                message,
                "❌ Refund record nahi ho saka."
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
                "⚠️ Refund save ho gaya, lekin deal complete nahi ho saki."
            )

            return

        # ==================================
        # USER NAME
        # ==================================

        user_name = (
            target_user.first_name
            or "User"
        )

        mention = user_mention(
            target_user_id,
            user_name
        )

        # ==================================
        # FORMAT AMOUNT
        # ==================================

        refund_text = (
            f"₹{holding_amount:g}"
        )

        # ==================================
        # REFUND MESSAGE
        # ==================================

        refund_message = bot.send_message(
            message.chat.id,
            (
                f"↩️ <b>PAYMENT REFUNDED — {refund_text}</b>\n\n"
                f"💸 <b>{refund_text} REFUNDED</b>\n"
                f"👤 <b>To:</b> {mention}\n\n"
                "✅ <b>Deal completed successfully.</b>"
            ),
            parse_mode="HTML"
        )

        # ==================================
        # PIN MESSAGE
        # ==================================

        try:

            bot.pin_chat_message(
                message.chat.id,
                refund_message.message_id,
                disable_notification=True
            )

        except Exception as error:

            print(
                f"Refund pin error: {error}"
            )

        # ==================================
        # DELETE COMMAND
        # ==================================

        delete_command_message(
            bot,
            message
              )
