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
        # COMMAND FORMAT
        # ==================================

        command_text = normalize_command(
            message.text
        )

        parts = command_text.split()

        if len(parts) != 2:

            bot.reply_to(
                message,
                (
                    "⚠️ Release amount do.\n\n"
                    "Example:\n"
                    "<code>.release 500</code>"
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

        raw_amount = (
            parts[1]
            .replace("₹", "")
            .replace("$", "")
            .strip()
        )

        try:

            amount = float(
                raw_amount
            )

        except ValueError:

            bot.reply_to(
                message,
                "⚠️ Amount valid number hona chahiye."
            )

            delete_command_message(
                bot,
                message
            )

            return

        if amount <= 0:

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
        # CHECK HOLD AMOUNT
        # ==================================

        holding_amount = (
            active_deal["holding_amount"]
            or 0
        )

        if holding_amount <= 0:

            bot.reply_to(
                message,
                "⚠️ Is deal mein koi amount hold nahi hai."
            )

            delete_command_message(
                bot,
                message
            )

            return

        if amount > holding_amount:

            bot.reply_to(
                message,
                (
                    f"⚠️ Release amount hold amount "
                    f"<b>₹{holding_amount:g}</b> se zyada nahi ho sakta."
                ),
                parse_mode="HTML"
            )

            delete_command_message(
                bot,
                message
            )

            return

        # ==================================
        # FIND RELEASE USER
        # ==================================

        # Agar MM kisi user ke message ko reply
        # karke .release karta hai, wahi user
        # release receiver maana jayega.

        if not message.reply_to_message:

            bot.reply_to(
                message,
                (
                    "⚠️ Jis user ko amount release karna hai, "
                    "uske message ko reply karke command bhejo.\n\n"
                    "Example:\n"
                    "<code>.release 500</code>"
                ),
                parse_mode="HTML"
            )

            delete_command_message(
                bot,
                message
            )

            return

        release_user = (
            message.reply_to_message.from_user
        )

        if not release_user:

            bot.reply_to(
                message,
                "⚠️ Release user identify nahi ho paya."
            )

            delete_command_message(
                bot,
                message
            )

            return

        release_user_id = release_user.id

        # ==================================
        # USER MUST BE IN DEAL
        # ==================================

        user_1_id = active_deal["user_1_id"]
        user_2_id = active_deal["user_2_id"]

        if release_user_id not in [
            user_1_id,
            user_2_id
        ]:

            bot.reply_to(
                message,
                "⚠️ Ye user is deal ka part nahi hai."
            )

            delete_command_message(
                bot,
                message
            )

            return

        # ==================================
        # SAVE RELEASE EVENT
        # ==================================

        success = record_release(
            deal_id=active_deal["deal_id"],
            user_id=release_user_id,
            amount=amount
        )

        if not success:

            bot.reply_to(
                message,
                "❌ Release save nahi ho paya."
            )

            delete_command_message(
                bot,
                message
            )

            return

        # ==================================
        # COMPLETE DEAL
        # ==================================

        complete_deal(
            active_deal["deal_id"]
        )

        # ==================================
        # USER NAME
        # ==================================

        user_name = (
            release_user.first_name
            or "User"
        )

        mention = (
            f'<a href="tg://user?id={release_user_id}">'
            f'{user_name}'
            f'</a>'
        )

        # ==================================
        # RELEASE MESSAGE
        # ==================================

        release_message = bot.send_message(
            message.chat.id,
            (
                "✅ <b>PAYMENT RELEASED</b>\n\n"
                f"💰 <b>₹{amount:g}</b> released to "
                f"{mention}\n\n"
                "🤝 <b>Deal completed successfully.</b>"
            ),
            parse_mode="HTML"
        )

        # ==================================
        # PIN
        # ==================================

        try:

            bot.pin_chat_message(
                message.chat.id,
                release_message.message_id,
                disable_notification=True
            )

        except Exception as error:

            print(
                f"Release pin error: {error}"
            )

        # ==================================
        # DELETE COMMAND
        # ==================================

        delete_command_message(
            bot,
            message
          )
