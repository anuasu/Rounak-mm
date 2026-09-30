from config import MM_CHAT_IDS, ADMIN_IDS

from database.database import (
    get_active_deal,
    update_payment
)


# ==========================================
# FORMAT USER MENTION
# ==========================================

def user_mention(user_id, name):

    safe_name = name or "User"

    return (
        f'<a href="tg://user?id={user_id}">'
        f'{safe_name}'
        f'</a>'
    )


# ==========================================
# REGISTER PAYMENT
# ==========================================

def register_payment(bot):

    @bot.message_handler(
        func=lambda message:
        message.text
        and message.text.strip().lower().startswith(".payment")
    )
    def payment_command(message):

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

            return

        # ==================================
        # GET PAYMENT TEXT
        # ==================================

        parts = message.text.strip().split()

        if len(parts) != 2:

            bot.reply_to(
                message,
                (
                    "⚠️ Payment amount do.\n\n"
                    "Examples:\n"
                    "<code>.payment 500</code>\n"
                    "<code>.payment ₹500</code>\n"
                    "<code>.payment $100</code>"
                ),
                parse_mode="HTML"
            )

            return

        raw_amount = parts[1].strip()

        # ==================================
        # CURRENCY
        # ==================================

        currency = "₹"

        if raw_amount.startswith("$"):
            currency = "$"
            raw_amount = raw_amount[1:]

        elif raw_amount.startswith("₹"):
            currency = "₹"
            raw_amount = raw_amount[1:]

        # ==================================
        # AMOUNT
        # ==================================

        try:
            amount = float(raw_amount)

        except ValueError:

            bot.reply_to(
                message,
                "⚠️ Amount valid number hona chahiye."
            )

            return

        if amount <= 0:

            bot.reply_to(
                message,
                "⚠️ Amount 0 se greater hona chahiye."
            )

            return

        # ==================================
        # SAVE PAYMENT
        # ==================================

        update_payment(
            active_deal["deal_id"],
            amount
        )

        # ==================================
        # GET USERS
        # ==================================

        user_1_id = active_deal["user_1_id"]
        user_2_id = active_deal["user_2_id"]

        try:
            user_1 = bot.get_chat(user_1_id)
            user_2 = bot.get_chat(user_2_id)

            user_1_name = (
                user_1.first_name
                or "User 1"
            )

            user_2_name = (
                user_2.first_name
                or "User 2"
            )

        except Exception:

            user_1_name = "User 1"
            user_2_name = "User 2"

        mention_1 = user_mention(
            user_1_id,
            user_1_name
        )

        mention_2 = user_mention(
            user_2_id,
            user_2_name
        )

        amount_text = f"{currency}{amount:g}"

        # ==================================
        # MESSAGE 1
        # ==================================

        payment_message = bot.send_message(
            message.chat.id,
            (
                "💸 <b>PAYMENT SENT</b>\n\n"
                f"{amount_text} sent.\n\n"
                "Please drop voucher."
            ),
            parse_mode="HTML"
        )

        # ==================================
        # PIN MESSAGE 1
        # ==================================

        try:
            bot.pin_chat_message(
                message.chat.id,
                payment_message.message_id,
                disable_notification=True
            )
        except Exception as error:
            print(
                f"Payment pin error: {error}"
            )

        # ==================================
        # MESSAGE 2
        # ==================================

        voucher_format_message = bot.send_message(
    message.chat.id,
    (
        "🧾 <b>VOUCHER FORMAT</b>\n\n"
        f"<code>I vouch @RounakMM for MM'D "
        f"{amount_text}</code>"
    ),
    parse_mode="HTML"
)

        # ==================================
        # PIN MESSAGE 2
        # ==================================

        try:
            bot.pin_chat_message(
                message.chat.id,
                voucher_format_message.message_id,
                disable_notification=True
            )
        except Exception as error:
            print(
                f"Voucher format pin error: {error}"
            )

        # ==================================
        # MESSAGE 3
        # ==================================

        reminder_message = bot.send_message(
            message.chat.id,
            (
                f"{mention_1} {mention_2}\n\n"
                f"📩 <b>Please drop voucher for "
                f"{amount_text}.</b>"
            ),
            parse_mode="HTML"
        )

        # ==================================
        # PIN MESSAGE 3
        # ==================================

        try:
            bot.pin_chat_message(
                message.chat.id,
                reminder_message.message_id,
                disable_notification=True
            )
        except Exception as error:
            print(
                f"Reminder pin error: {error}"
      )
