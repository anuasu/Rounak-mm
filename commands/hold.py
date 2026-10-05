from config import MM_CHAT_IDS, ADMIN_IDS

from database.database import (
    get_active_deal,
    update_holding
)

from commands.command_utils import (
    normalize_command,
    delete_command_message
)


# ==========================================
# MM FEE CALCULATOR
# ==========================================

def calculate_mm_fee(amount):

    if 10 <= amount <= 49:
        return 10

    elif 50 <= amount <= 349:
        return 20

    elif 350 <= amount <= 499:
        return 30

    elif 500 <= amount <= 699:
        return 40

    elif 700 <= amount <= 999:
        return 50

    elif 1000 <= amount <= 1499:
        return 80

    elif 1500 <= amount <= 1999:
        return 100

    elif 2000 <= amount <= 2499:
        return 130

    elif 2500 <= amount <= 2999:
        return 160

    elif amount >= 3000:
        extra_slabs = int((amount - 3000) // 500)
        return 190 + (extra_slabs * 30)

    return None


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
# REGISTER HOLD
# ==========================================

def register_hold(bot):

    @bot.message_handler(
        func=lambda message:
        message.text
        and normalize_command(message.text)
        .lower()
        .startswith(".hold")
    )
    def hold_command(message):

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
        # AMOUNT CHECK
        # ==================================

        if len(parts) != 2:

            bot.reply_to(
                message,
                (
                    "⚠️ Hold amount do.\n\n"
                    "Example:\n"
                    "<code>.hold 100</code>"
                ),
                parse_mode="HTML"
            )

            delete_command_message(
                bot,
                message
            )

            return

        raw_amount = (
            parts[1]
            .replace("₹", "")
            .strip()
        )

        try:

            hold_amount = float(
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

        if hold_amount < 10:

            bot.reply_to(
                message,
                "⚠️ Minimum hold amount ₹10 hai."
            )

            delete_command_message(
                bot,
                message
            )

            return

        # ==================================
        # CALCULATE MM FEE
        # ==================================

        mm_fee = calculate_mm_fee(
            hold_amount
        )

        if mm_fee is None:

            bot.reply_to(
                message,
                "⚠️ Is amount ke liye MM fee set nahi hai."
            )

            delete_command_message(
                bot,
                message
            )

            return

        received_amount = (
            hold_amount + mm_fee
        )

        # ==================================
        # SAVE HOLDING + FEE + TIME
        # ==================================

        update_holding(
            active_deal["deal_id"],
            hold_amount,
            mm_fee,
            received_amount
        )

        # ==================================
        # GET USERS
        # ==================================

        user_1_id = active_deal["user_1_id"]
        user_2_id = active_deal["user_2_id"]

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
                f"Hold user lookup error: {error}"
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
        # FORMAT AMOUNTS
        # ==================================

        hold_text = f"₹{hold_amount:g}"
        fee_text = f"₹{mm_fee:g}"
        received_text = f"₹{received_amount:g}"

        # ==================================
        # HOLD MESSAGE
        # ==================================

        hold_message = bot.send_message(
            message.chat.id,
            (
                f"🔒 <b>PAYMENT ON HOLD — {hold_text}</b>\n\n"

                f"💰 <b>{received_text} RECEIVED</b>\n"
                f"🔐 <b>{hold_text} HOLD</b>\n"
                f"💸 <b>{fee_text} MM FEE</b>\n\n"

                "📩 <b>Please continue your deal in DM.</b>\n\n"

                f"👤 {mention_1}\n"
                f"👤 {mention_2}"
            ),
            parse_mode="HTML"
        )

        # ==================================
        # PIN MESSAGE
        # ==================================

        try:

            bot.pin_chat_message(
                message.chat.id,
                hold_message.message_id,
                disable_notification=True
            )

        except Exception as error:

            print(
                f"Hold pin error: {error}"
            )

        # ==================================
        # DELETE COMMAND
        # ==================================

        delete_command_message(
            bot,
            message
        )
