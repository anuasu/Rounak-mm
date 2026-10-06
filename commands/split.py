from config import MM_CHAT_IDS, ADMIN_IDS

from database.database import (
    get_active_deal,
    record_split,
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
# REGISTER SPLIT
# ==========================================

def register_split(bot):

    @bot.message_handler(
        func=lambda message:
        message.text
        and (
            normalize_command(message.text)
            .lower()
            .startswith(".split")
            or
            normalize_command(message.text)
            .lower()
            .startswith(".50-50")
        )
    )
    def split_command(message):

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
        # GET BOTH DEAL USERS
        # ==================================

        user_1_id = active_deal["user_1_id"]
        user_2_id = active_deal["user_2_id"]

        # ==================================
        # 50-50 CALCULATION
        # ==================================

        split_amount = holding_amount / 2

        # ==================================
        # RECORD SPLIT
        # ==================================

        success = record_split(
            active_deal["deal_id"],
            user_1_id,
            split_amount,
            user_2_id,
            split_amount
        )

        if not success:

            bot.reply_to(
                message,
                "❌ Split record nahi ho saka."
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
                "⚠️ Split save ho gaya, lekin deal complete nahi ho saki."
            )

            return

        # ==================================
        # GET USER DETAILS
        # ==================================

        try:

            user_1 = bot.get_chat(
                user_1_id
            )

            user_2 = bot.get_chat(
                user_2_id
            )

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
                f"Split user lookup error: {error}"
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
        # FORMAT AMOUNT
        # ==================================

        total_text = (
            f"₹{holding_amount:g}"
        )

        split_text = (
            f"₹{split_amount:g}"
        )

        # ==================================
        # SEND RESULT
        # ==================================

        split_message = bot.send_message(
            message.chat.id,
            (
                f"⚖️ <b>50-50 SPLIT — {total_text}</b>\n\n"

                f"👤 {mention_1} → "
                f"<b>{split_text}</b>\n"

                f"👤 {mention_2} → "
                f"<b>{split_text}</b>\n\n"

                "✅ <b>Deal completed successfully.</b>"
            ),
            parse_mode="HTML"
        )

        # ==================================
        # PIN RESULT
        # ==================================

        try:

            bot.pin_chat_message(
                message.chat.id,
                split_message.message_id,
                disable_notification=True
            )

        except Exception as error:

            print(
                f"Split pin error: {error}"
            )

        # ==================================
        # DELETE COMMAND
        # ==================================

        delete_command_message(
            bot,
            message
          )
