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
# group_id -> split information
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
# PARSE AMOUNT
# ==========================================================

def parse_amount(text):

    if not text:
        return None, None

    raw = text.strip()

    currency = "₹"

    if raw.startswith("$"):
        currency = "$"
        raw = raw[1:].strip()

    elif raw.startswith("₹"):
        raw = raw[1:].strip()

    try:
        amount = float(raw)

    except (ValueError, TypeError):
        return None, None

    if amount <= 0:
        return None, None

    return amount, currency


# ==========================================================
# FORMAT AMOUNT
# ==========================================================

def format_amount(amount, currency="₹"):

    return f"{currency}{amount:g}"


# ==========================================================
# GET USER FROM CURRENT DEAL
# ==========================================================

def get_deal_user(active_deal, user_id):

    if not active_deal:
        return None

    if user_id == active_deal["user_1_id"]:

        return get_user(
            active_deal["user_1_id"]
        )

    if user_id == active_deal["user_2_id"]:

        return get_user(
            active_deal["user_2_id"]
        )

    return None


# ==========================================================
# CHECK MM
# ==========================================================

def is_mm(message):

    return (
        message.from_user
        and message.from_user.id in MM_CHAT_IDS
    )


# ==========================================================
# START SPLIT
# ==========================================================

def register_split(bot):

    @bot.message_handler(
        func=lambda message: (
            message.text
            and normalize_command(
                message.text
            ).strip().lower() == ".split"
        )
    )
    def split_command(message):

        # ======================================================
        # MM ONLY
        # ======================================================

        if not is_mm(message):

            if (
                message.from_user
                and message.from_user.id in ADMIN_IDS
            ):

                bot.reply_to(
                    message,
                    "⚠️ Sirf MM ye command use kar sakta hai."
                )

            return

        # ======================================================
        # GROUP ONLY
        # ======================================================

        if message.chat.type not in (
            "group",
            "supergroup"
        ):

            bot.reply_to(
                message,
                "⚠️ .split sirf group mein use kar sakte ho."
            )

            return

        group_id = message.chat.id

        # ======================================================
        # ACTIVE DEAL
        # ======================================================

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

        # ======================================================
        # EXISTING SPLIT
        # ======================================================

        old_data = pending_split.get(
            group_id
        )

        if old_data:

            # Different deal = remove old broken state
            if (
                old_data.get("deal_id")
                != active_deal.get("deal_id")
            ):

                pending_split.pop(
                    group_id,
                    None
                )

            else:

                bot.reply_to(
                    message,
                    (
                        "⚠️ Split already active hai.\n\n"
                        "Current step complete karo."
                    )
                )

                delete_command_message(
                    bot,
                    message
                )

                return

        # ======================================================
        # CREATE NEW SPLIT
        # ======================================================

        pending_split[group_id] = {

            "deal_id":
                active_deal["deal_id"],

            "step":
                "release"
        }

        # ======================================================
        # ASK RELEASE
        # ======================================================

        bot.send_message(
            group_id,
            (
                "✂️ <b>SPLIT DEAL</b>\n\n"

                "💸 <b>Release wale user ke message ko "
                "reply karke:</b>\n\n"

                "<code>.r AMOUNT</code>\n\n"

                "Example:\n"
                "<code>.r 80</code>\n\n"

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
# HANDLE .r / .f REPLIES
# ==========================================================

def register_split_input(bot):

    @bot.message_handler(
        func=lambda message: (
            message.chat.type in (
                "group",
                "supergroup"
            )
            and message.chat.id in pending_split
            and message.text
            and message.reply_to_message is not None
            and (
                normalize_command(
                    message.text
                ).strip().lower().startswith(".r")
                or
                normalize_command(
                    message.text
                ).strip().lower().startswith(".f")
            )
        )
    )
    def split_reply_handler(message):

        # ======================================================
        # MM ONLY
        # ======================================================

        if not is_mm(message):
            return

        group_id = message.chat.id

        data = pending_split.get(
            group_id
        )

        if not data:
            return

        # ======================================================
        # ACTIVE DEAL
        # ======================================================

        active_deal = get_active_deal(
            group_id
        )

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

        # ======================================================
        # DEAL ID CHECK
        # ======================================================

        if (
            data.get("deal_id")
            != active_deal.get("deal_id")
        ):

            pending_split.pop(
                group_id,
                None
            )

            bot.reply_to(
                message,
                "⚠️ Current deal change ho chuki hai."
            )

            return

        # ======================================================
        # REPLIED USER
        # ======================================================

        replied_message = (
            message.reply_to_message
        )

        replied_user = (
            replied_message.from_user
        )

        if not replied_user:
            return

        # Don't allow bot messages
        if replied_user.is_bot:

            bot.reply_to(
                message,
                "⚠️ Kisi real deal user ke message ko reply karo."
            )

            return

        replied_user_id = (
            replied_user.id
        )

        # ======================================================
        # COMMAND PARSE
        # ======================================================

        command_text = normalize_command(
            message.text
        ).strip()

        parts = command_text.split()

        # Must be exactly:
        #
        # .r 80
        # OR
        # .f 120
        #

        if len(parts) != 2:

            bot.reply_to(
                message,
                (
                    "⚠️ Correct format:\n\n"
                    "<code>.r 80</code>\n"
                    "or\n"
                    "<code>.f 120</code>"
                ),
                parse_mode="HTML"
            )

            return

        command = parts[0].lower()

        # ======================================================
        # IMPORTANT:
        # EXACT COMMAND ONLY
        # ======================================================

        if command not in (
            ".r",
            ".f"
        ):

            return

        # ======================================================
        # AMOUNT
        # ======================================================

        amount, currency = parse_amount(
            parts[1]
        )

        if amount is None:

            bot.reply_to(
                message,
                (
                    "⚠️ Amount valid hona chahiye.\n\n"
                    "Example:\n"
                    "<code>.r 80</code>"
                ),
                parse_mode="HTML"
            )

            return

        # ======================================================
        # RELEASE STEP
        # ======================================================

        if data.get("step") == "release":

            # First step MUST be .r
            if command != ".r":

                bot.reply_to(
                    message,
                    (
                        "⚠️ Abhi release amount chahiye.\n\n"
                        "Release user ke message ko reply "
                        "karke:\n"
                        "<code>.r AMOUNT</code>\n\n"
                        "Example:\n"
                        "<code>.r 80</code>"
                    ),
                    parse_mode="HTML"
                )

                return

            # --------------------------------------------------
            # CHECK USER IS IN CURRENT DEAL
            # --------------------------------------------------

            release_user = get_deal_user(
                active_deal,
                replied_user_id
            )

            if not release_user:

                bot.reply_to(
                    message,
                    (
                        "⚠️ Jis user ke message ko reply "
                        "kiya hai, wo current deal ka "
                        "part nahi hai."
                    )
                )

                return

            release_name = (
                release_user["first_name"]
                or replied_user.first_name
                or "User"
            )

            # --------------------------------------------------
            # SAVE RELEASE
            # --------------------------------------------------

            pending_split[group_id] = {

                "deal_id":
                    active_deal["deal_id"],

                "release_user_id":
                    replied_user_id,

                "release_user_name":
                    release_name,

                "release_amount":
                    amount,

                "currency":
                    currency,

                "step":
                    "refund"
            }

            # --------------------------------------------------
            # ASK REFUND
            # --------------------------------------------------

            bot.send_message(
                group_id,
                (
                    "↩️ <b>NOW REFUND USER</b>\n\n"

                    "💸 <b>Refund wale user ke message "
                    "ko reply karke:</b>\n\n"

                    "<code>.f AMOUNT</code>\n\n"

                    "Example:\n"
                    "<code>.f 120</code>\n\n"

                    "⚠️ User ke message ko reply karna "
                    "zaroori hai."
                ),
                parse_mode="HTML"
            )

            delete_command_message(
                bot,
                message
            )

            return

        # ======================================================
        # REFUND STEP
        # ======================================================

        if data.get("step") != "refund":
            return

        # ------------------------------------------------------
        # Second step MUST be .f
        # ------------------------------------------------------

        if command != ".f":

            bot.reply_to(
                message,
                (
                    "⚠️ Abhi refund amount chahiye.\n\n"
                    "Refund user ke message ko reply "
                    "karke:\n"
                    "<code>.f AMOUNT</code>\n\n"
                    "Example:\n"
                    "<code>.f 120</code>"
                ),
                parse_mode="HTML"
            )

            return

        # ------------------------------------------------------
        # CHECK REFUND USER
        # ------------------------------------------------------

        refund_user = get_deal_user(
            active_deal,
            replied_user_id
        )

        if not refund_user:

            bot.reply_to(
                message,
                (
                    "⚠️ Jis user ke message ko reply "
                    "kiya hai, wo current deal ka "
                    "part nahi hai."
                )
            )

            return

        refund_user_id = (
            replied_user_id
        )

        # ------------------------------------------------------
        # SAME USER CHECK
        # ------------------------------------------------------

        if (
            refund_user_id
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

        # ======================================================
        # RECORD SPLIT
        # ======================================================

        success = record_split(

            deal_id=
                data["deal_id"],

            refund_user_id=
                refund_user_id,

            refund_amount=
                amount,

            release_user_id=
                data["release_user_id"],

            release_amount=
                data["release_amount"]
        )

        # ======================================================
        # DATABASE FAILED
        # ======================================================

        if not success:

            bot.reply_to(
                message,
                (
                    "❌ Split complete nahi ho saka.\n\n"
                    "Possible reason: deal already "
                    "completed ho chuki hai."
                )
            )

            pending_split.pop(
                group_id,
                None
            )

            return

        # ======================================================
        # AMOUNTS
        # ======================================================

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

        final_currency = (
            currency
            or data.get("currency")
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

        # ======================================================
        # CLEAR STATE
        # ======================================================

        pending_split.pop(
            group_id,
            None
        )

        # ======================================================
        # MENTIONS
        # ======================================================

        release_mention = user_mention(
            data["release_user_id"],
            data["release_user_name"]
        )

        refund_mention = user_mention(
            refund_user_id,
            refund_name
        )

        # ======================================================
        # PAYMENT MESSAGE
        # ======================================================

        payment_message = bot.send_message(
            group_id,
            (
                "💸 <b>MMD PAYMENT</b>\n\n"

                f"💰 {release_text} → "
                f"{release_mention}\n"

                f"↩️ {refund_text} → "
                f"{refund_mention}\n\n"

                f"💵 <b>Total: "
                f"{total_text}</b>\n\n"

                "Please drop voucher."
            ),
            parse_mode="HTML"
        )

        # ======================================================
        # PIN PAYMENT
        # ======================================================

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

        # ======================================================
        # VOUCHER
        #
        # IMPORTANT:
        # Release + Refund = voucher amount
        # ======================================================

        bot.send_message(
            group_id,
            (
                f"<code>I vouch @RounakMM "
                f"for MMD payment "
                f"{total_text}</code>"
            ),
            parse_mode="HTML"
        )

        # ======================================================
        # VOUCHER REQUEST
        # ======================================================

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

        # ======================================================
        # SPLIT INFORMATION
        # ======================================================

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

        # ======================================================
        # DELETE .f MESSAGE
        # ======================================================

        delete_command_message(
            bot,
            message
        )
