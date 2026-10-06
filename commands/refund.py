from config import MM_CHAT_IDS, ADMIN_IDS

from database.database import (
    get_active_deal,
    finalize_deal
)

from commands.command_utils import (
    normalize_command,
    delete_command_message
)


# ==========================================
# USER MENTION
# ==========================================

def user_mention(user_id, name):

    safe_name = name or "User"

    return (
        f'<a href="tg://user?id={user_id}">'
        f'{safe_name}'
        f'</a>'
    )


# ==========================================
# REGISTER REFUND
# ==========================================

def register_refund(bot):

    @bot.message_handler(
        func=lambda message:
        message.text
        and normalize_command(
            message.text
        ).lower().startswith(".refund")
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

        group_id = message.chat.id

        # ==================================
        # ACTIVE DEAL
        # ==================================

        active_deal = get_active_deal(
            group_id
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
        # COMMAND
        #
        # .refund AMOUNT
        #
        # Example:
        # .refund 500
        # .refund ₹500
        # .refund $100
        # ==================================

        command_text = normalize_command(
            message.text
        )

        parts = command_text.split()

        if len(parts) != 2:

            bot.reply_to(
                message,
                (
                    "⚠️ Refund format galat hai.\n\n"
                    "Use:\n"
                    "<code>.refund AMOUNT</code>\n\n"
                    "Example:\n"
                    "<code>.refund 500</code>"
                ),
                parse_mode="HTML"
            )

            delete_command_message(
                bot,
                message
            )

            return

        # ==================================
        # AMOUNT
        # ==================================

        raw_amount = parts[1].strip()

        currency = "₹"

        if raw_amount.startswith("$"):

            currency = "$"
            raw_amount = raw_amount[1:]

        elif raw_amount.startswith("₹"):

            raw_amount = raw_amount[1:]

        try:

            refund_amount = float(
                raw_amount
            )

        except ValueError:

            bot.reply_to(
                message,
                "⚠️ Refund amount valid number hona chahiye."
            )

            delete_command_message(
                bot,
                message
            )

            return

        if refund_amount <= 0:

            bot.reply_to(
                message,
                "⚠️ Amount 0 se greater hona chahiye."
            )

            delete_command_message(
                bot,
                message
            )

            return

        # ==================================
        # REFUND USER
        #
        # Reply to user's message:
        # .refund 500
        # ==================================

        if not message.reply_to_message:

            bot.reply_to(
                message,
                (
                    "⚠️ Jisko refund karna hai "
                    "uske message ko reply karke command bhejo.\n\n"
                    "Example:\n"
                    "<code>.refund 500</code>"
                ),
                parse_mode="HTML"
            )

            delete_command_message(
                bot,
                message
            )

            return

        refund_user = (
            message.reply_to_message.from_user
        )

        if not refund_user or refund_user.is_bot:

            bot.reply_to(
                message,
                "⚠️ Valid refund user select karo."
            )

            delete_command_message(
                bot,
                message
            )

            return

        refund_user_id = refund_user.id

        # ==================================
        # DEAL USERS
        # ==================================

        user_1_id = active_deal["user_1_id"]
        user_2_id = active_deal["user_2_id"]

        # ==================================
        # CHECK USER
        # ==================================

        if refund_user_id not in [
            user_1_id,
            user_2_id
        ]:

            bot.reply_to(
                message,
                "⚠️ Ye user current deal ka part nahi hai."
            )

            delete_command_message(
                bot,
                message
            )

            return

        # ==================================
        # OTHER USER
        # ==================================

        if refund_user_id == user_1_id:

            other_user_id = user_2_id

        else:

            other_user_id = user_1_id

        # ==================================
        # GET USER DETAILS
        # ==================================

        try:

            refund_chat = bot.get_chat(
                refund_user_id
            )

            other_chat = bot.get_chat(
                other_user_id
            )

            refund_name = (
                refund_chat.first_name
                or "User"
            )

            other_name = (
                other_chat.first_name
                or "User"
            )

        except Exception as error:

            print(
                f"Refund user lookup error: {error}"
            )

            refund_name = (
                refund_user.first_name
                or "User"
            )

            other_name = "User"

        # ==================================
        # FINALIZE DEAL
        #
        # BOTH USERS:
        # + refund amount
        # + 1 completed deal
        #
        # Same leaderboard behaviour
        # as previous .payment flow.
        # ==================================

        success = finalize_deal(
            active_deal["deal_id"],
            "refund",
            {
                user_1_id: refund_amount,
                user_2_id: refund_amount
            }
        )

        if not success:

            bot.reply_to(
                message,
                (
                    "❌ Refund complete nahi ho saka.\n"
                    "Deal already completed ho sakti hai."
                )
            )

            delete_command_message(
                bot,
                message
            )

            return

        # ==================================
        # AMOUNT TEXT
        # ==================================

        amount_text = (
            f"{currency}{refund_amount:g}"
        )

        # ==================================
        # MENTIONS
        # ==================================

        refund_mention = user_mention(
            refund_user_id,
            refund_name
        )

        other_mention = user_mention(
            other_user_id,
            other_name
        )

        # ==================================
        # MESSAGE 1
        # REFUND SENT
        # ==================================

        refund_message = bot.send_message(
            group_id,
            (
                "↩️ <b>REFUND SENT</b>\n\n"

                f"{amount_text} refunded to "
                f"{refund_mention}.\n\n"

                "Please drop voucher."
            ),
            parse_mode="HTML"
        )

        # ==================================
        # PIN REFUND MESSAGE
        # ==================================

        try:

            bot.pin_chat_message(
                group_id,
                refund_message.message_id,
                disable_notification=True
            )

        except Exception as error:

            print(
                f"Refund pin error: {error}"
            )

        # ==================================
        # MESSAGE 2
        # VOUCHER
        # ==================================

        bot.send_message(
            group_id,
            (
                f"<code>I vouch @RounakMM "
                f"for refund {amount_text}</code>"
            ),
            parse_mode="HTML"
        )

        # ==================================
        # MESSAGE 3
        # VOUCHER REQUEST
        # ==================================

        bot.send_message(
            group_id,
            (
                f"{refund_mention} {other_mention}\n\n"
                f"📩 <b>Please drop voucher "
                f"for {amount_text}.</b>"
            ),
            parse_mode="HTML"
        )

        # ==================================
        # MESSAGE 4
        # REFUND INFO
        # ==================================

        bot.send_message(
            group_id,
            (
                "↩️ <b>REFUND COMPLETED</b>\n\n"

                f"👤 <b>Refunded To:</b> "
                f"{refund_mention}\n"

                f"💰 <b>Refund Amount:</b> "
                f"{amount_text}\n"

                f"🤝 <b>Deal:</b> "
                f"#{active_deal['deal_id']}\n\n"

                "📊 Leaderboard updated.\n"
                "✅ Deal completed."
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
