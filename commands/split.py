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


# ==========================================================
# TEMPORARY SPLIT STATE
#
# group_id -> split data
# ==========================================================

pending_split = {}


# ==========================================================
# USER MENTION
# ==========================================================

def user_mention(user_id, name):

    safe_name = name or "User"

    return (
        f'<a href="tg://user?id={user_id}">'
        f'{safe_name}'
        f'</a>'
    )


# ==========================================================
# AMOUNT PARSER
# ==========================================================

def parse_amount(value):

    if not value:
        return None, None

    value = value.strip()

    currency = "₹"

    if value.startswith("$"):
        currency = "$"
        value = value[1:].strip()

    elif value.startswith("₹"):
        value = value[1:].strip()

    try:
        amount = float(value)
    except (ValueError, TypeError):
        return None, None

    if amount <= 0:
        return None, None

    return amount, currency


# ==========================================================
# AMOUNT FORMAT
# ==========================================================

def format_amount(amount, currency="₹"):

    return f"{currency}{amount:g}"


# ==========================================================
# MM CHECK
# ==========================================================

def is_mm(message):

    return message.from_user.id in MM_CHAT_IDS


# ==========================================================
# GET DEAL USER
# ==========================================================

def get_deal_user(active_deal, user_id):

    if not active_deal:
        return None

    if user_id == active_deal["user_1_id"]:
        return get_user(user_id)

    if user_id == active_deal["user_2_id"]:
        return get_user(user_id)

    return None


# ==========================================================
# START .SPLIT
# ==========================================================

def register_split(bot):

    @bot.message_handler(
        func=lambda message: (
            message.text
            and normalize_command(message.text)
            .strip()
            .lower()
            == ".split"
        )
    )
    def split_command(message):

        # --------------------------------------------------
        # MM ONLY
        # --------------------------------------------------

        if not is_mm(message):

            if message.from_user.id in ADMIN_IDS:

                bot.reply_to(
                    message,
                    "⚠️ Sirf MM ye command use kar sakta hai."
                )

            return

        # --------------------------------------------------
        # GROUP ONLY
        # --------------------------------------------------

        if message.chat.type not in (
            "group",
            "supergroup"
        ):
            return

        group_id = message.chat.id

        # --------------------------------------------------
        # ACTIVE DEAL
        # --------------------------------------------------

        active_deal = get_active_deal(group_id)

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

        # --------------------------------------------------
        # OLD STATE CHECK
        # --------------------------------------------------

        old_data = pending_split.get(group_id)

        if old_data:

            if old_data.get("deal_id") == active_deal["deal_id"]:

                bot.reply_to(
                    message,
                    (
                        "⚠️ Split already setup hai.\n\n"
                        "Ab .split dobara mat likho.\n"
                        "Bot ke next step ko follow karo."
                    )
                )

                delete_command_message(
                    bot,
                    message
                )

                return

            # Old deal ka stale state
            pending_split.pop(
                group_id,
                None
            )

        # --------------------------------------------------
        # CREATE SPLIT STATE
        # --------------------------------------------------

        pending_split[group_id] = {

            "deal_id":
                active_deal["deal_id"],

            "step":
                "release",

            "release_user_id":
                None,

            "release_user_name":
                None,

            "release_amount":
                None,

            "release_currency":
                "₹"
        }

        # --------------------------------------------------
        # ASK RELEASE
        # --------------------------------------------------

        bot.send_message(
            group_id,
            (
                "✂️ <b>SPLIT DEAL</b>\n\n"

                "💸 Release wale user ke message ko "
                "reply karke command bhejo:\n\n"

                "<code>.release AMOUNT</code>\n\n"

                "Example:\n"
                "<code>.release 80</code>\n\n"

                "⚠️ User ke message ko reply karna "
                "zaroori hai."
            ),
            parse_mode="HTML"
        )

        delete_command_message(
            bot,
            message
        )


# ==========================================================
# HANDLE .RELEASE / .REFUND
# ==========================================================

def register_split_input(bot):

    @bot.message_handler(
        func=lambda message: (
            message.chat.type in (
                "group",
                "supergroup"
            )
            and message.chat.id in pending_split
            and message.text is not None
            and normalize_command(message.text)
            .strip()
            .lower()
            .startswith((".release", ".refund"))
        )
    )
    def split_command_input(message):

        # ==================================================
        # MM ONLY
        # ==================================================

        if not is_mm(message):
            return

        group_id = message.chat.id

        data = pending_split.get(group_id)

        if not data:
            return

        # ==================================================
        # ACTIVE DEAL
        # ==================================================

        active_deal = get_active_deal(group_id)

        if not active_deal:

            pending_split.pop(
                group_id,
                None
            )

            bot.reply_to(
                message,
                "⚠️ Active deal nahi mila."
            )

            return

        # ==================================================
        # DEAL CHECK
        # ==================================================

        if data.get("deal_id") != active_deal.get("deal_id"):

            pending_split.pop(
                group_id,
                None
            )

            bot.reply_to(
                message,
                "⚠️ Current deal change ho chuka hai. .split dobara karo."
            )

            return

        # ==================================================
        # MUST REPLY TO USER MESSAGE
        # ==================================================

        if not message.reply_to_message:

            if data.get("step") == "release":

                bot.reply_to(
                    message,
                    (
                        "⚠️ Release user ke message ko "
                        "reply karke command bhejo.\n\n"
                        "<code>.release 80</code>"
                    ),
                    parse_mode="HTML"
                )

            else:

                bot.reply_to(
                    message,
                    (
                        "⚠️ Refund user ke message ko "
                        "reply karke command bhejo.\n\n"
                        "<code>.refund 100</code>"
                    ),
                    parse_mode="HTML"
                )

            return

        # ==================================================
        # GET REPLIED USER
        # ==================================================

        replied_user = (
            message.reply_to_message.from_user
        )

        if not replied_user:
            return

        if replied_user.is_bot:
            return

        replied_user_id = replied_user.id

        # ==================================================
        # PARSE COMMAND
        # ==================================================

        command_text = normalize_command(
            message.text
        ).strip()

        parts = command_text.split()

        if len(parts) != 2:

            if data.get("step") == "release":

                bot.reply_to(
                    message,
                    (
                        "⚠️ Correct format:\n"
                        "<code>.release 80</code>"
                    ),
                    parse_mode="HTML"
                )

            else:

                bot.reply_to(
                    message,
                    (
                        "⚠️ Correct format:\n"
                        "<code>.refund 100</code>"
                    ),
                    parse_mode="HTML"
                )

            return

        command = parts[0].lower()

        raw_amount = parts[1]

        amount, currency = parse_amount(
            raw_amount
        )

        if amount is None:

            bot.reply_to(
                message,
                (
                    "⚠️ Valid amount enter karo.\n\n"
                    "Example:\n"
                    "<code>.release 80</code>"
                ),
                parse_mode="HTML"
            )

            return

        # ==================================================
        # RELEASE STEP
        # ==================================================

        if data.get("step") == "release":

            # ----------------------------------------------
            # ONLY .RELEASE ALLOWED
            # ----------------------------------------------

            if command != ".release":

                bot.reply_to(
                    message,
                    (
                        "⚠️ Abhi release amount chahiye.\n\n"
                        "Use:\n"
                        "<code>.release 80</code>\n\n"
                        "User ke message ko reply karke."
                    ),
                    parse_mode="HTML"
                )

                return

            # ----------------------------------------------
            # CHECK DEAL USER
            # ----------------------------------------------

            release_user = get_deal_user(
                active_deal,
                replied_user_id
            )

            if not release_user:

                bot.reply_to(
                    message,
                    (
                        "⚠️ Jis user ko reply kiya hai "
                        "wo current deal ka part nahi hai."
                    )
                )

                return

            # ----------------------------------------------
            # USER NAME
            # ----------------------------------------------

            release_name = (
                release_user["first_name"]
                or replied_user.first_name
                or "User"
            )

            # ----------------------------------------------
            # SAVE RELEASE
            # ----------------------------------------------

            data["release_user_id"] = (
                replied_user_id
            )

            data["release_user_name"] = (
                release_name
            )

            data["release_amount"] = (
                amount
            )

            data["release_currency"] = (
                currency
            )

            data["step"] = "refund"

            pending_split[group_id] = data

            # ----------------------------------------------
            # ASK REFUND
            # ----------------------------------------------

            bot.send_message(
                group_id,
                (
                    "↩️ <b>NOW REFUND</b>\n\n"

                    "Refund wale user ke message ko "
                    "reply karke command bhejo:\n\n"

                    "<code>.refund AMOUNT</code>\n\n"

                    "Example:\n"
                    "<code>.refund 100</code>\n\n"

                    "⚠️ User ke message ko reply karna "
                    "zaroori hai."
                ),
                parse_mode="HTML"
            )

            # Delete .release command
            delete_command_message(
                bot,
                message
            )

            return

        # ==================================================
        # REFUND STEP
        # ==================================================

        if data.get("step") == "refund":

            # ----------------------------------------------
            # ONLY .REFUND ALLOWED
            # ----------------------------------------------

            if command != ".refund":

                bot.reply_to(
                    message,
                    (
                        "⚠️ Abhi refund amount chahiye.\n\n"
                        "Use:\n"
                        "<code>.refund 100</code>\n\n"
                        "User ke message ko reply karke."
                    ),
                    parse_mode="HTML"
                )

                return

            # ----------------------------------------------
            # CHECK DEAL USER
            # ----------------------------------------------

            refund_user = get_deal_user(
                active_deal,
                replied_user_id
            )

            if not refund_user:

                bot.reply_to(
                    message,
                    (
                        "⚠️ Jis user ko reply kiya hai "
                        "wo current deal ka part nahi hai."
                    )
                )

                return

            # ----------------------------------------------
            # SAME USER CHECK
            # ----------------------------------------------

            if (
                replied_user_id
                == data["release_user_id"]
            ):

                bot.reply_to(
                    message,
                    (
                        "⚠️ Release aur refund user "
                        "same nahi ho sakte."
                    )
                )

                return

            refund_name = (
                refund_user["first_name"]
                or replied_user.first_name
                or "User"
            )

            # ----------------------------------------------
            # RECORD SPLIT
            # ----------------------------------------------

            success = record_split(

                deal_id=
                    data["deal_id"],

                refund_user_id=
                    replied_user_id,

                refund_amount=
                    amount,

                release_user_id=
                    data["release_user_id"],

                release_amount=
                    data["release_amount"]
            )

            if not success:

                pending_split.pop(
                    group_id,
                    None
                )

                bot.reply_to(
                    message,
                    (
                        "❌ Split complete nahi ho saka.\n"
                        "Deal already completed ho sakti hai."
                    )
                )

                return

            # ==================================================
            # AMOUNTS
            # ==================================================

            release_amount = (
                data["release_amount"]
            )

            refund_amount = (
                amount
            )

            total_amount = (
                release_amount
                + refund_amount
            )

            # Use release currency as final currency
            final_currency = (
                data.get("release_currency")
                or currency
                or "₹"
            )

            release_text = format_amount(
                release_amount,
                final_currency
            )

            refund_text = format_amount(
                refund_amount,
                final_currency
            )

            total_text = format_amount(
                total_amount,
                final_currency
            )

            # ==================================================
            # CLEAR STATE
            # ==================================================

            pending_split.pop(
                group_id,
                None
            )

            # ==================================================
            # MENTIONS
            # ==================================================

            release_mention = user_mention(
                data["release_user_id"],
                data["release_user_name"]
            )

            refund_mention = user_mention(
                replied_user_id,
                refund_name
            )

            # ==================================================
            # PAYMENT MESSAGE
            # ==================================================

            payment_message = bot.send_message(
                group_id,
                (
                    "💸 <b>MMD PAYMENT</b>\n\n"

                    f"💰 {release_text} → "
                    f"{release_mention}\n"

                    f"↩️ {refund_text} → "
                    f"{refund_mention}\n\n"

                    f"💵 <b>Total: {total_text}</b>\n\n"

                    "Please drop voucher."
                ),
                parse_mode="HTML"
            )

            # ==================================================
            # PIN
            # ==================================================

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

            # ==================================================
            # COMBINED VOUCHER
            # ==================================================

            bot.send_message(
                group_id,
                (
                    f"<code>I vouch @RounakMM "
                    f"for MMD payment "
                    f"{total_text}</code>"
                ),
                parse_mode="HTML"
            )

            # ==================================================
            # VOUCHER REQUEST
            # ==================================================

            bot.send_message(
                group_id,
                (
                    f"{release_mention} "
                    f"{refund_mention}\n\n"

                    f"📩 <b>Please drop voucher "
                    f"for {total_text}.</b>"
                ),
                parse_mode="HTML"
            )

            # ==================================================
            # SPLIT INFORMATION
            # ==================================================

            bot.send_message(
                group_id,
                (
                    "✂️ <b>SPLIT COMPLETED</b>\n\n"

                    f"💸 <b>Release:</b> "
                    f"{release_mention} — "
                    f"{release_text}\n"

                    f"↩️ <b>Refund:</b> "
                    f"{refund_mention} — "
                    f"{refund_text}\n\n"

                    f"💰 <b>Total MMD Payment:</b> "
                    f"{total_text}\n\n"

                    f"🤝 <b>Deal:</b> "
                    f"#{data['deal_id']}\n\n"

                    "📊 Leaderboard updated.\n"
                    "✅ Deal completed."
                ),
                parse_mode="HTML"
            )

            # ==================================================
            # DELETE .REFUND COMMAND
            # ==================================================

            delete_command_message(
                bot,
                message
            )

            return
