from config import MM_CHAT_IDS, ADMIN_IDS

from database.database import get_active_deal


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
# REGISTER VOUCHER
# ==========================================

def register_voucher(bot):

    @bot.message_handler(
        func=lambda message:
        message.text
        and message.text.strip().lower().startswith(".voucher")
    )
    def voucher_command(message):

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

            return

        # ==================================
        # AMOUNT
        # ==================================

        parts = message.text.strip().split()

        if len(parts) != 2:

            bot.reply_to(
                message,
                (
                    "⚠️ Amount do.\n\n"
                    "Example:\n"
                    "<code>.voucher 500</code>"
                ),
                parse_mode="HTML"
            )

            return

        raw_amount = (
            parts[1]
            .replace("₹", "")
            .replace("$", "")
            .strip()
        )

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
        # AMOUNT FORMAT
        # ==================================

        amount_text = f"₹{amount:g}"

        # ==================================
        # VOUCHER MESSAGE
        # ==================================

        voucher_message = bot.send_message(
            message.chat.id,
            (
                f"<code>I vouch @RounakMM "
                f"for MM'D {amount_text}</code>"
            ),
            parse_mode="HTML"
        )

        # ==================================
        # GET DEAL USERS
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

        except Exception as error:

            print(
                f"Voucher user lookup error: {error}"
            )

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

        # ==================================
        # REPLY WITH BOTH USERS
        # ==================================

        bot.reply_to(
            voucher_message,
            (
                f"👤 {mention_1}\n"
                f"👤 {mention_2}"
            ),
            parse_mode="HTML"
        )
