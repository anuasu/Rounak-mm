from config import MM_CHAT_IDS, ADMIN_IDS


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
        # GET AMOUNT
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

        # ==================================
        # VALIDATE AMOUNT
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
        # FORMAT AMOUNT
        # ==================================

        amount_text = f"₹{amount:g}"

        # ==================================
        # SEND VOUCHER
        # ==================================

        bot.send_message(
            message.chat.id,
            (
                f"<code>I vouch @RounakMM "
                f"for MM'D {amount_text}</code>"
            ),
            parse_mode="HTML"
        )
