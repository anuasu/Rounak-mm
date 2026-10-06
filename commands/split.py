from config import MM_CHAT_IDS, ADMIN_IDS

from database.database import (
    get_active_deal,
    record_split,
    get_user
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
# CLEAN USERNAME
# ==========================================

def clean_username(username):

    username = username.strip()

    if username.startswith("@"):
        username = username[1:]

    return username.lower()


# ==========================================
# FIND USER IN CURRENT DEAL
# ==========================================

def find_deal_user(active_deal, username):

    username = clean_username(username)

    user_1_id = active_deal["user_1_id"]
    user_2_id = active_deal["user_2_id"]

    # --------------------------------------
    # USER 1
    # --------------------------------------

    user_1 = get_user(user_1_id)

    if user_1:

        saved_username = (
            user_1["username"] or ""
        )

        if (
            saved_username
            and clean_username(saved_username) == username
        ):
            return user_1

    # --------------------------------------
    # USER 2
    # --------------------------------------

    user_2 = get_user(user_2_id)

    if user_2:

        saved_username = (
            user_2["username"] or ""
        )

        if (
            saved_username
            and clean_username(saved_username) == username
        ):
            return user_2

    return None


# ==========================================
# REGISTER SPLIT
# ==========================================

def register_split(bot):

    @bot.message_handler(
        func=lambda message:
        message.text
        and normalize_command(
            message.text
        ).lower() == ".split"
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

                "Release wale user ka username aur amount bhejo.\n\n"

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
# HANDLE RELEASE SIDE
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

        # ==================================
        # ONLY RELEASE STEP
        # ==================================

        if data.get("step") != "release":
            return

        command_text = normalize_command(
            message.text
        )

        parts = command_text.split()

        # ==================================
        # FORMAT
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

        username = parts[1]

        raw_amount = parts[2]

        # ==================================
        # CURRENCY
        # ==================================

        currency = "₹"

        if raw_amount.startswith("$"):

            currency = "$"
            raw_amount = raw_amount[1:]

        elif raw_amount.startswith("₹"):

            raw_amount = raw_amount[1:]

        # ==================================
        # AMOUNT
        # ==================================

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
        # GET ACTIVE DEAL AGAIN
        # ==================================

        active_deal = get_active_deal(
            group_id
        )

        if not active_deal:

            pending_split.pop(
                group_id,
                None
            )

            return

        # ==================================
        # FIND USER FROM USERNAME
        # ==================================

        release_user = find_deal_user(
            active_deal,
            username
        )

        if not release_user:

            bot.reply_to(
                message,
                (
                    "⚠️ Ye username current deal "
                    "mein nahi mila.\n\n"
                    "Saved username check karo."
                )
            )

            delete_command_message(
                bot,
                message
            )

            return

        release_user_id = release_user["chat_id"]

        release_name = (
            release_user["first_name"]
            or "User"
        )

        # ==================================
        # SAVE RELEASE SIDE
        # ==================================

        pending_split[group_id] = {
            "deal_id": active_deal["deal_id"],
            "release_user_id": release_user_id,
            "release_username": (
                release_user["username"]
                or username
            ),
            "release_user_name": release_name,
            "release_amount": amount,
            "currency": currency,
            "step": "refund"
        }

        bot.send_message(
            group_id,
            (
                "🔄 <b>NOW REFUND USER</b>\n\n"

                "Refund wale user ka username aur amount bhejo.\n\n"

                "Example:\n"
                "<code>.split @username 40</code>"
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
        # FORMAT
        # ==================================

        if len(parts) != 3:

            bot.reply_to(
                message,
                (
                    "⚠️ Format:\n"
                    "<code>.split @username 40</code>"
                ),
                parse_mode="HTML"
            )

            delete_command_message(
                bot,
                message
            )

            return

        username = parts[1]

        raw_amount = parts[2]

        currency = data.get(
            "currency",
            "₹"
        )

        if raw_amount.startswith("$"):

            currency = "$"
            raw_amount = raw_amount[1:]

        elif raw_amount.startswith("₹"):

            raw_amount = raw_amount[1:]

        # ==================================
        # AMOUNT
        # ==================================

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
        # ACTIVE DEAL
        # ==================================

        active_deal = get_active_deal(
            group_id
        )

        if not active_deal:

            pending_split.pop(
                group_id,
                None
            )

            return

        # ==================================
        # FIND REFUND USER
        # ==================================

        refund_user = find_deal_user(
            active_deal,
            username
        )

        if not refund_user:

            bot.reply_to(
                message,
                (
                    "⚠️ Ye username current deal "
                    "mein nahi mila."
                )
            )

            delete_command_message(
                bot,
                message
            )

            return

        refund_user_id = refund_user["chat_id"]

        refund_name = (
            refund_user["first_name"]
            or "User"
        )

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
        # CLEAR TEMP DATA
        # ==================================

        pending_split.pop(
            group_id,
            None
        )

        # ==================================
        # AMOUNTS
        # ==================================

        release_amount = data[
            "release_amount"
        ]

        release_amount_text = (
            f"{currency}{release_amount:g}"
        )

        refund_amount_text = (
            f"{currency}{refund_amount:g}"
        )

        # ==================================
        # PAYMENT MESSAGE
        # ==================================

        payment_message = bot.send_message(
            group_id,
            (
                "💸 <b>PAYMENT SENT</b>\n\n"

                f"💰 {release_amount_text} → "
                f"<b>{data['release_user_name']}</b>\n"

                f"↩️ {refund_amount_text} → "
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
                f"{release_amount_text} + "
                f"{refund_amount_text}</code>"
            ),
            parse_mode="HTML"
        )

        # ==================================
        # USER MENTIONS
        # ==================================

        release_mention = user_mention(
            data["release_user_id"],
            data["release_user_name"]
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

        # ==================================
        # DELETE COMMAND
        # ==================================

        delete_command_message(
            bot,
            message
        )
