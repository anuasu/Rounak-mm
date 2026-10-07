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
# GET USER NAME
# ==========================================

def get_user_name(bot, user_id):

    try:

        chat = bot.get_chat(user_id)

        return (
            chat.first_name
            or "User"
        )

    except Exception as error:

        print(
            f"Split user lookup error: {error}"
        )

        user = get_user(user_id)

        if user:

            return (
                user["first_name"]
                or "User"
            )

        return "User"


# ==========================================
# REGISTER SPLIT COMMAND
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
            "step": "refund"
        }

        bot.send_message(
            group_id,
            (
                "✂️ <b>SPLIT DEAL</b>\n\n"

                "↩️ Refund wale user ke message ko "
                "reply karke sirf refund amount bhejo.\n\n"

                "Example:\n"
                "<code>60</code>\n\n"

                "⚠️ <b>.split dobara likhne ki "
                "zaroorat nahi hai.</b>"
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
        # CURRENT STEP
        # ==================================

        step = data.get("step")

        # ==================================
        # REFUND SIDE
        # ==================================

        if step == "refund":

            # ----------------------------------
            # MUST REPLY
            # ----------------------------------

            if not message.reply_to_message:

                bot.reply_to(
                    message,
                    (
                        "⚠️ Refund wale user ke "
                        "message ko reply karke amount bhejo.\n\n"
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

            # ----------------------------------
            # REFUND USER
            # ----------------------------------

            refund_user = (
                message.reply_to_message.from_user
            )

            if not refund_user or refund_user.is_bot:

                bot.reply_to(
                    message,
                    "⚠️ Valid refund user ko reply karo."
                )

                delete_command_message(
                    bot,
                    message
                )

                return

            refund_user_id = refund_user.id

            # ----------------------------------
            # CHECK DEAL USER
            # ----------------------------------

            if refund_user_id not in [
                active_deal["user_1_id"],
                active_deal["user_2_id"]
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

            # ----------------------------------
            # AMOUNT
            # ----------------------------------

            raw_amount = (
                message.text.strip()
            )

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
                    "⚠️ Sirf valid amount bhejo. Example: 60"
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

            # ----------------------------------
            # SAVE REFUND SIDE
            # ----------------------------------

            refund_name = (
                refund_user.first_name
                or get_user_name(
                    bot,
                    refund_user_id
                )
            )

            pending_split[group_id] = {
                "deal_id": active_deal["deal_id"],
                "refund_user_id": refund_user_id,
                "refund_user_name": refund_name,
                "refund_amount": refund_amount,
                "currency": currency,
                "step": "release"
            }

            # ----------------------------------
            # ASK RELEASE SIDE
            # ----------------------------------

            bot.send_message(
                group_id,
                (
                    "💸 <b>REFUND SIDE SAVED</b>\n\n"

                    f"↩️ Refund: <b>"
                    f"{currency}{refund_amount:g}</b>\n"
                    f"👤 User: {user_mention(refund_user_id, refund_name)}\n\n"

                    "➡️ Ab <b>release wale user</b> ke "
                    "message ko reply karke sirf release amount bhejo.\n\n"

                    "Example:\n"
                    "<code>40</code>\n\n"

                    "⚠️ <b>.split dobara likhne ki "
                    "zaroorat nahi hai.</b>"
                ),
                parse_mode="HTML"
            )

            delete_command_message(
                bot,
                message
            )

            return

        # ==================================
        # RELEASE SIDE
        # ==================================

        if step == "release":

            # ----------------------------------
            # MUST REPLY
            # ----------------------------------

            if not message.reply_to_message:

                bot.reply_to(
                    message,
                    (
                        "⚠️ Release wale user ke "
                        "message ko reply karke amount bhejo.\n\n"
                        "Example:\n"
                        "<code>40</code>"
                    ),
                    parse_mode="HTML"
                )

                delete_command_message(
                    bot,
                    message
                )

                return

            # ----------------------------------
            # RELEASE USER
            # ----------------------------------

            release_user = (
                message.reply_to_message.from_user
            )

            if not release_user or release_user.is_bot:

                bot.reply_to(
                    message,
                    "⚠️ Valid release user ko reply karo."
                )

                delete_command_message(
                    bot,
                    message
                )

                return

            release_user_id = release_user.id

            # ----------------------------------
            # CHECK DEAL USER
            # ----------------------------------

            if release_user_id not in [
                active_deal["user_1_id"],
                active_deal["user_2_id"]
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

            # ----------------------------------
            # SAME USER CHECK
            # ----------------------------------

            if release_user_id == data["refund_user_id"]:

                bot.reply_to(
                    message,
                    (
                        "⚠️ Refund aur release user "
                        "same nahi ho sakte."
                    )
                )

                delete_command_message(
                    bot,
                    message
                )

                return

            # ----------------------------------
            # AMOUNT
            # ----------------------------------

            raw_amount = (
                message.text.strip()
            )

            currency = data.get(
                "currency",
                "₹"
            )

            if raw_amount.startswith("$"):

                currency = "$"
                raw_amount = raw_amount[1:]

            elif raw_amount.startswith("₹"):

                raw_amount = raw_amount[1:]

            try:

                release_amount = float(
                    raw_amount
                )

            except ValueError:

                bot.reply_to(
                    message,
                    "⚠️ Sirf valid amount bhejo. Example: 40"
                )

                delete_command_message(
                    bot,
                    message
                )

                return

            if release_amount <= 0:

                bot.reply_to(
                    message,
                    "⚠️ Amount 0 se greater hona chahiye."
                )

                delete_command_message(
                    bot,
                    message
                )

                return

            # ----------------------------------
            # RELEASE NAME
            # ----------------------------------

            release_name = (
                release_user.first_name
                or get_user_name(
                    bot,
                    release_user_id
                )
            )

            # ==================================
            # CHECK TOTAL AGAINST DEAL
            # ==================================

            total_split = (
                data["refund_amount"]
                + release_amount
            )

            available_amount = max(
                float(active_deal["holding_amount"] or 0),
                float(active_deal["total_received"] or 0),
                float(active_deal["deal_amount"] or 0)
            )

            if total_split > available_amount:

                bot.reply_to(
                    message,
                    (
                        "❌ Split amount available amount "
                        "se zyada hai.\n\n"
                        f"Available: <b>"
                        f"{currency}{available_amount:g}</b>\n"
                        f"Requested: <b>"
                        f"{currency}{total_split:g}</b>"
                    ),
                    parse_mode="HTML"
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
                refund_user_id=data["refund_user_id"],
                refund_amount=data["refund_amount"],
                release_user_id=release_user_id,
                release_amount=release_amount
            )

            if not success:

                bot.reply_to(
                    message,
                    (
                        "❌ Split complete nahi ho saka.\n\n"
                        "Deal already completed ho sakti hai "
                        "ya amount invalid ho sakta hai."
                    )
                )

                pending_split.pop(
                    group_id,
                    None
                )

                delete_command_message(
                    bot,
                    message
                )

                return

            # ==================================
            # CLEAR TEMP DATA
            # ==================================

            pending_split.pop(
                group_id,
                None
            )

            refund_amount = data[
                "refund_amount"
            ]

            # ==================================
            # AMOUNT TEXT
            # ==================================

            refund_amount_text = (
                f"{currency}{refund_amount:g}"
            )

            release_amount_text = (
                f"{currency}{release_amount:g}"
            )

            # ==================================
            # MENTIONS
            # ==================================

            refund_mention = user_mention(
                data["refund_user_id"],
                data["refund_user_name"]
            )

            release_mention = user_mention(
                release_user_id,
                release_name
            )

            # ==================================
            # SPLIT COMPLETED
            # ==================================

            split_message = bot.send_message(
                group_id,
                (
                    "✂️ <b>SPLIT DEAL COMPLETED</b>\n\n"

                    f"↩️ <b>Refund:</b> "
                    f"{refund_amount_text} → "
                    f"{refund_mention}\n"

                    f"💸 <b>Release:</b> "
                    f"{release_amount_text} → "
                    f"{release_mention}\n\n"

                    f"🤝 <b>Deal:</b> "
                    f"#{data['deal_id']}\n\n"

                    "📊 Leaderboard updated.\n"
                    "✅ Both users' deal completed."
                ),
                parse_mode="HTML"
            )

            # ==================================
            # PIN SPLIT INFO
            # ==================================

            try:

                bot.pin_chat_message(
                    group_id,
                    split_message.message_id,
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
                    f"for split deal "
                    f"{refund_amount_text} + "
                    f"{release_amount_text}</code>"
                ),
                parse_mode="HTML"
            )

            # ==================================
            # VOUCHER REQUEST
            # ==================================

            bot.send_message(
                group_id,
                (
                    f"{refund_mention} {release_mention}\n\n"
                    "📩 <b>Please drop voucher.</b>"
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
