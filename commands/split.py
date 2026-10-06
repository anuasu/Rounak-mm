from config import MM_CHAT_IDS, ADMIN_IDS

from database.database import (
    get_active_deal,
    record_split
)

from commands.command_utils import (
    normalize_command,
    delete_command_message
)


# ==========================================
# TEMPORARY SPLIT SETUP
# group_chat_id -> split data
# ==========================================

pending_split = {}


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
# REGISTER SPLIT
# ==========================================

def register_split(bot):

    @bot.message_handler(
        func=lambda message:
        message.text
        and normalize_command(message.text).lower() == ".split"
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

            bot.reply_to(
                message,
                "❌ .split sirf group mein use kar sakte ho."
            )

            delete_command_message(
                bot,
                message
            )

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
        # CHECK EXISTING SPLIT
        # ==================================

        if group_id in pending_split:

            bot.reply_to(
                message,
                "⚠️ Split already setup ho raha hai."
            )

            delete_command_message(
                bot,
                message
            )

            return

        # ==================================
        # START SPLIT
        # ==================================

        pending_split[group_id] = {
            "deal_id": active_deal["deal_id"],
            "step": "release"
        }

        bot.send_message(
            group_id,
            (
                "✂️ <b>SPLIT DEAL</b>\n\n"

                "👤 <b>Release user</b> ko reply karke "
                "<code>.split</code> dobara bhejo.\n\n"

                "Example:\n"
                "<code>.split @username 60</code>"
            ),
            parse_mode="HTML"
        )

        delete_command_message(
            bot,
            message
        )


# ==========================================
# HANDLE SPLIT INPUT
# ==========================================

def register_split_input(bot):

    @bot.message_handler(
        func=lambda message:
        message.chat.type in [
            "group",
            "supergroup"
        ]
        and message.chat.id in pending_split
        and message.text
    )
    def split_input(message):

        # ==================================
        # MM ONLY
        # ==================================

        if message.from_user.id not in MM_CHAT_IDS:
            return

        group_id = message.chat.id

        data = pending_split.get(
            group_id
        )

        if not data:
            return

        command_text = normalize_command(
            message.text
        )

        parts = command_text.split()

        # ==================================
        # EXPECT:
        # .split USER AMOUNT
        # ==================================

        if len(parts) != 3:

            bot.reply_to(
                message,
                (
                    "⚠️ Format:\n"
                    "<code>.split @username 60</code>"
                ),
                parse_mode="HTML"
            )

            delete_command_message(
                bot,
                message
            )

            return

        # ==================================
        # USER
        # ==================================

        user_text = parts[1]

        # ==================================
        # AMOUNT
        # ==================================

        raw_amount = parts[2]

        currency = "₹"

        if raw_amount.startswith("$"):

            currency = "$"
            raw_amount = raw_amount[1:]

        elif raw_amount.startswith("₹"):

            raw_amount = raw_amount[1:]

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
        # GET REPLY USER
        # ==================================

        if not message.reply_to_message:

            bot.reply_to(
                message,
                (
                    "⚠️ User ke message ko reply karke "
                    "command bhejo."
                )
            )

            delete_command_message(
                bot,
                message
            )

            return

        user = message.reply_to_message.from_user

        if not user or user.is_bot:

            bot.reply_to(
                message,
                "⚠️ Valid user select karo."
            )

            delete_command_message(
                bot,
                message
            )

            return

        # ==================================
        # CHECK USER IS IN DEAL
        # ==================================

        user_id = user.id

        user_1_id = data["user_1_id"] \
            if "user_1_id" in data \
            else None

        user_2_id = data["user_2_id"] \
            if "user_2_id" in data \
            else None

        active_deal = get_active_deal(
            group_id
        )

        if not active_deal:

            pending_split.pop(
                group_id,
                None
            )

            return

        user_1_id = active_deal["user_1_id"]
        user_2_id = active_deal["user_2_id"]

        if user_id not in [
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
        # SAVE RELEASE USER
        # ==================================

        pending_split[group_id] = {
            "deal_id": active_deal["deal_id"],
            "release_user_id": user_id,
            "release_user_name": user.first_name or "User",
            "release_amount": amount,
            "step": "refund"
        }

        bot.send_message(
            group_id,
            (
                "🔄 <b>NOW REFUND USER</b>\n\n"

                "Refund wale user ke message ko "
                "reply karke command bhejo.\n\n"

                "Example:\n"
                "<code>.split 40</code>"
            ),
            parse_mode="HTML"
        )

        delete_command_message(
            bot,
            message
        )


# ==========================================
# HANDLE REFUND SIDE
# ==========================================

def register_split_refund(bot):

    @bot.message_handler(
        func=lambda message:
        message.chat.type in [
            "group",
            "supergroup"
        ]
        and message.chat.id in pending_split
        and message.text
    )
    def split_refund(message):

        # ==================================
        # MM ONLY
        # ==================================

        if message.from_user.id not in MM_CHAT_IDS:
            return

        group_id = message.chat.id

        data = pending_split.get(
            group_id
        )

        if not data:
            return

        if data.get("step") != "refund":
            return

        command_text = normalize_command(
            message.text
        )

        parts = command_text.split()

        # ==================================
        # .split AMOUNT
        # ==================================

        if len(parts) != 2:

            bot.reply_to(
                message,
                (
                    "⚠️ Format:\n"
                    "<code>.split 40</code>"
                ),
                parse_mode="HTML"
            )

            delete_command_message(
                bot,
                message
            )

            return

        raw_amount = parts[1]

        if raw_amount.startswith("₹"):
            raw_amount = raw_amount[1:]

        try:

            refund_amount = float(
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
        # REPLY USER
        # ==================================

        if not message.reply_to_message:

            bot.reply_to(
                message,
                "⚠️ Refund user ke message ko reply karo."
            )

            delete_command_message(
                bot,
                message
            )

            return

        refund_user = message.reply_to_message.from_user

        if not refund_user or refund_user.is_bot:
            return

        refund_user_id = refund_user.id

        # ==================================
        # ACTIVE DEAL
        # ==================================

        active_deal = get_active_deal(
            group_id
        )

        if not active_deal:
            return

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
        # SAME USER CHECK
        # ==================================

        if refund_user_id == data["release_user_id"]:

            bot.reply_to(
                message,
                "⚠️ Release aur refund user same nahi ho sakte."
            )

            delete_command_message(
                bot,
                message
            )

            return

        # ==================================
        # RECORD SPLIT
        # ==================================

        success = record_split(
            deal_id=data["deal_id"],
            refund_user_id=refund_user_id,
            refund_amount=refund_amount,
            release_user_id=data["release_user_id"],
            release_amount=data["release_amount"]
        )

        if not success:

            bot.reply_to(
                message,
                "❌ Split complete nahi ho saka."
            )

            pending_split.pop(
                group_id,
                None
            )

            return

        # ==================================
        # CLEAR
        # ==================================

        pending_split.pop(
            group_id,
            None
        )

        # ==================================
        # USER NAMES
        # ==================================

        release_name = (
            data["release_user_name"]
            or "User"
        )

        refund_name = (
            refund_user.first_name
            or "User"
        )

        release_amount = data["release_amount"]

        # ==================================
        # PAYMENT MESSAGE
        # ==================================

        payment_message = bot.send_message(
            group_id,
            (
                "💸 <b>PAYMENT SENT</b>\n\n"

                f"💰 ₹{release_amount:g} → "
                f"<b>{release_name}</b>\n"

                f"↩️ ₹{refund_amount:g} → "
                f"<b>{refund_name}</b>\n\n"

                "Please drop voucher."
            ),
            parse_mode="HTML"
        )

        # ==================================
        # PIN
        # ==================================

        try:

            bot.pin_chat_message(
                group_id,
                payment_message.message_id,
                disable_notification=True
            )

        except Exception as error:

            print(
                f"Split pin error: {error}"
            )

        # ==================================
        # VOUCHER MESSAGE
        # ==================================

        bot.send_message(
            group_id,
            (
                f"<code>I vouch @RounakMM "
                f"for split payment "
                f"₹{release_amount:g} + "
                f"₹{refund_amount:g}</code>"
            ),
            parse_mode="HTML"
        )

        # ==================================
        # USER MENTION
        # ==================================

        release_mention = user_mention(
            data["release_user_id"],
            release_name
        )

        refund_mention = user_mention(
            refund_user_id,
            refund_name
        )

        bot.send_message(
            group_id,
            (
                f"{release_mention} {refund_mention}\n\n"
                f"📩 <b>Please drop voucher.</b>"
            ),
            parse_mode="HTML"
        )

        delete_command_message(
            bot,
            message
        )
