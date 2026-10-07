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
#
# group_id -> split data
# ==========================================

pending_split = {}


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
# PARSE AMOUNT
# ==========================================

def parse_amount(raw_amount):

    raw_amount = str(raw_amount).strip()

    currency = "₹"

    if raw_amount.startswith("$"):
        currency = "$"
        raw_amount = raw_amount[1:].strip()

    elif raw_amount.startswith("₹"):
        raw_amount = raw_amount[1:].strip()

    try:
        amount = float(raw_amount)
    except (ValueError, TypeError):
        return None, None

    if amount <= 0:
        return None, None

    return amount, currency


# ==========================================
# GET REPLIED USER
# ==========================================

def get_replied_user(message):

    if not message.reply_to_message:
        return None

    user = message.reply_to_message.from_user

    if not user:
        return None

    if user.is_bot:
        return None

    return user


# ==========================================
# REGISTER SPLIT COMMAND
# ==========================================

def register_split(bot):

    @bot.message_handler(
        func=lambda message:
        message.text
        and normalize_command(
            message.text
        ).lower().split()[0:1] == [".split"]
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
        # ONLY .SPLIT
        # ==================================

        command_text = normalize_command(
            message.text
        )

        parts = command_text.split()

        if len(parts) != 1:

            bot.reply_to(
                message,
                (
                    "⚠️ Ab username/amount nahi dena hai.\n\n"
                    "Sirf:\n"
                    "<code>.split</code>\n\n"
                    "Uske baad user ke message ko "
                    "reply karke amount bhejna hai."
                ),
                parse_mode="HTML"
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
        # EXISTING SPLIT
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
        #
        # FIRST = REFUND
        # ==================================

        pending_split[group_id] = {
            "deal_id": active_deal["deal_id"],
            "user_1_id": active_deal["user_1_id"],
            "user_2_id": active_deal["user_2_id"],
            "step": "refund"
        }

        bot.send_message(
            group_id,
            (
                "✂️ <b>SPLIT DEAL</b>\n\n"

                "↩️ Refund wale user ke message ko "
                "reply karke <b>sirf refund amount</b> bhejo.\n\n"

                "Example:\n"
                "<code>120</code>\n\n"

                "⚠️ <code>.split</code> dobara likhne ki "
                "zaroorat nahi hai."
            ),
            parse_mode="HTML"
        )

        delete_command_message(
            bot,
            message
        )


# ==========================================
# REGISTER SPLIT INPUT
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
        # CURRENT STEP
        # ==================================

        step = data.get("step")

        if step not in [
            "refund",
            "release"
        ]:
            return

        # ==================================
        # MUST REPLY
        # ==================================

        replied_user = get_replied_user(
            message
        )

        if not replied_user:

            if step == "refund":

                bot.reply_to(
                    message,
                    (
                        "⚠️ Refund wale user ke "
                        "message ko reply karke "
                        "sirf amount bhejo.\n\n"
                        "Example:\n"
                        "<code>120</code>"
                    ),
                    parse_mode="HTML"
                )

            else:

                bot.reply_to(
                    message,
                    (
                        "⚠️ Release wale user ke "
                        "message ko reply karke "
                        "sirf amount bhejo.\n\n"
                        "Example:\n"
                        "<code>60</code>"
                    ),
                    parse_mode="HTML"
                )

            delete_command_message(
                bot,
                message
            )

            return

        # ==================================
        # USER MUST BE DEAL USER
        # ==================================

        user_id = replied_user.id

        if user_id not in [
            data["user_1_id"],
            data["user_2_id"]
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
        # AMOUNT
        # ==================================

        raw_amount = message.text.strip()

        # Only amount allowed
        if len(raw_amount.split()) != 1:

            bot.reply_to(
                message,
                (
                    "⚠️ Sirf amount bhejo.\n\n"
                    "Example:\n"
                    "<code>120</code>"
                ),
                parse_mode="HTML"
            )

            delete_command_message(
                bot,
                message
            )

            return

        amount, currency = parse_amount(
            raw_amount
        )

        if amount is None:

            bot.reply_to(
                message,
                "⚠️ Amount valid number hona chahiye."
            )

            delete_command_message(
                bot,
                message
            )

            return

        # ==================================
        # REFUND STEP
        # ==================================

        if step == "refund":

            refund_user_id = user_id

            # ----------------------------------
            # SAVE REFUND
            # ----------------------------------

            data["refund_user_id"] = refund_user_id
            data["refund_user_name"] = (
                replied_user.first_name
                or "User"
            )
            data["refund_username"] = (
                replied_user.username
                or ""
            )
            data["refund_amount"] = amount
            data["currency"] = currency
            data["step"] = "release"

            pending_split[group_id] = data

            # ----------------------------------
            # ASK RELEASE
            # ----------------------------------

            bot.send_message(
                group_id,
                (
                    "💸 <b>REFUND AMOUNT SET</b>\n\n"

                    f"↩️ Refund: "
                    f"<b>{currency}{amount:g}</b>\n\n"

                    "➡️ Ab <b>release wale user</b> ke "
                    "message ko reply karke "
                    "<b>sirf release amount</b> bhejo.\n\n"

                    "Example:\n"
                    "<code>60</code>\n\n"

                    "⚠️ <code>.split</code> dobara "
                    "likhne ki zaroorat nahi hai."
                ),
                parse_mode="HTML"
            )

            delete_command_message(
                bot,
                message
            )

            return

        # ==================================
        # RELEASE STEP
        # ==================================

        if step == "release":

            release_user_id = user_id

            # ----------------------------------
            # SAME USER CHECK
            # ----------------------------------

            if release_user_id == data.get(
                "refund_user_id"
            ):

                bot.reply_to(
                    message,
                    (
                        "⚠️ Refund aur release user "
                        "same nahi ho sakte.\n\n"
                        "Dusre deal user ke message ko "
                        "reply karke amount bhejo."
                    )
                )

                delete_command_message(
                    bot,
                    message
                )

                return

            # ----------------------------------
            # SAVE RELEASE
            # ----------------------------------

            release_name = (
                replied_user.first_name
                or "User"
            )

            refund_amount = data[
                "refund_amount"
            ]

            refund_user_id = data[
                "refund_user_id"
            ]

            refund_name = data[
                "refund_user_name"
            ]

            # ==================================
            # RECORD SPLIT
            # ==================================

            success = record_split(
                deal_id=data["deal_id"],
                refund_user_id=refund_user_id,
                refund_amount=refund_amount,
                release_user_id=release_user_id,
                release_amount=amount
            )

            if not success:

                bot.reply_to(
                    message,
                    (
                        "❌ Split complete nahi ho saka.\n"
                        "Deal already completed ho sakti hai."
                    )
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
            # AMOUNT TEXT
            # ==================================

            refund_amount_text = (
                f"{data.get('currency', '₹')}"
                f"{refund_amount:g}"
            )

            release_amount_text = (
                f"{currency}"
                f"{amount:g}"
            )

            # ==================================
            # PAYMENT MESSAGE
            # ==================================

            payment_message = bot.send_message(
                group_id,
                (
                    "✂️ <b>SPLIT COMPLETED</b>\n\n"

                    f"↩️ <b>Refund:</b> "
                    f"{refund_amount_text} → "
                    f"{refund_name}\n"

                    f"💸 <b>Release:</b> "
                    f"{release_amount_text} → "
                    f"{release_name}\n\n"

                    f"🤝 <b>Deal:</b> "
                    f"#{data['deal_id']}\n\n"

                    "📊 Leaderboard updated.\n"
                    "🧾 Please drop voucher."
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
            # VOUCHER
            # ==================================

            bot.send_message(
                group_id,
                (
                    f"<code>I vouch @RounakMM "
                    f"for split "
                    f"{refund_amount_text} + "
                    f"{release_amount_text}</code>"
                ),
                parse_mode="HTML"
            )

            # ==================================
            # USER MENTIONS
            # ==================================

            refund_mention = user_mention(
                refund_user_id,
                refund_name
            )

            release_mention = user_mention(
                release_user_id,
                release_name
            )

            bot.send_message(
                group_id,
                (
                    f"{refund_mention} "
                    f"{release_mention}\n\n"
                    "📩 <b>Please drop voucher.</b>"
                ),
                parse_mode="HTML"
            )

            # ==================================
            # DELETE AMOUNT MESSAGE
            # ==================================

            delete_command_message(
                bot,
                message
            )
