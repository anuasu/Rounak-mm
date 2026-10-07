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
# CHECK MM
# ==========================================================

def is_mm(message):

    return message.from_user.id in MM_CHAT_IDS


# ==========================================================
# START SPLIT
# ==========================================================

def register_split(bot):

    @bot.message_handler(
        func=lambda message: (
            message.text
            and normalize_command(message.text).strip().lower()
            == ".split"
        )
    )
    def split_command(message):

        # ------------------------------------------------------
        # MM ONLY
        # ------------------------------------------------------

        if not is_mm(message):

            if message.from_user.id in ADMIN_IDS:

                bot.reply_to(
                    message,
                    "⚠️ Sirf MM ye command use kar sakta hai."
                )

            return

        # ------------------------------------------------------
        # GROUP ONLY
        # ------------------------------------------------------

        if message.chat.type not in (
            "group",
            "supergroup"
        ):
            return

        group_id = message.chat.id

        # ------------------------------------------------------
        # ACTIVE DEAL
        # ------------------------------------------------------

        active_deal = get_active_deal(group_id)

        if not active_deal:

            bot.reply_to(
                message,
                "⚠️ Is group mein koi active deal nahi hai."
            )

            delete_command_message(bot, message)

            return

        # ------------------------------------------------------
        # RESET STALE STATE
        # ------------------------------------------------------

        old = pending_split.get(group_id)

        if old:

            if old.get("deal_id") != active_deal["deal_id"]:

                pending_split.pop(
                    group_id,
                    None
                )

            else:

                bot.reply_to(
                    message,
                    (
                        "⚠️ Split already setup hai.\n\n"
                        "Ab .split dobara mat likho.\n"
                        "Bot ke message ke according "
                        "user ke message ko reply karke amount bhejo."
                    )
                )

                delete_command_message(
                    bot,
                    message
                )

                return

        # ------------------------------------------------------
        # CREATE STATE
        # ------------------------------------------------------

        pending_split[group_id] = {
            "deal_id": active_deal["deal_id"],
            "step": "release"
        }

        # ------------------------------------------------------
        # ASK RELEASE
        # ------------------------------------------------------

        bot.send_message(
            group_id,
            (
                "✂️ <b>SPLIT DEAL</b>\n\n"

                "💸 <b>Release wale user ke message ko "
                "reply karke sirf release amount bhejo.</b>\n\n"

                "Example:\n"
                "<code>120</code>\n\n"

                "⚠️ <code>.split</code> dobara likhne "
                "ki zaroorat nahi hai."
            ),
            parse_mode="HTML"
        )

        delete_command_message(
            bot,
            message
        )


# ==========================================================
# HANDLE REPLY AMOUNTS
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
            and message.reply_to_message is not None
        )
    )
    def split_reply_handler(message):

        # ======================================================
        # MM ONLY
        # ======================================================

        if not is_mm(message):
            return

        group_id = message.chat.id

        data = pending_split.get(group_id)

        if not data:
            return

        # ======================================================
        # GET ACTIVE DEAL
        # ======================================================

        active_deal = get_active_deal(group_id)

        if not active_deal:

            pending_split.pop(
                group_id,
                None
            )

            return

        # ======================================================
        # DEAL CHECK
        # ======================================================

        if data.get("deal_id") != active_deal.get("deal_id"):

            pending_split.pop(
                group_id,
                None
            )

            return

        # ======================================================
        # GET REPLIED USER
        # ======================================================

        replied_message = message.reply_to_message

        replied_user = replied_message.from_user

        if not replied_user:
            return

        if replied_user.is_bot:
            return

        replied_user_id = replied_user.id

        # ======================================================
        # PARSE AMOUNT
        # ======================================================

        amount, currency = parse_amount(
            message.text
        )

        if amount is None:

            bot.reply_to(
                message,
                (
                    "⚠️ Sirf amount bhejo.\n\n"
                    "Example:\n"
                    "<code>120</code>"
                ),
                parse_mode="HTML"
            )

            return

        # ======================================================
        # RELEASE STEP
        # ======================================================

        if data.get("step") == "release":

            release_user = get_deal_user(
                active_deal,
                replied_user_id
            )

            if not release_user:

                bot.reply_to(
                    message,
                    (
                        "⚠️ Jis user ke message ko "
                        "reply kiya hai, wo current deal "
                        "ka part nahi hai."
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

                    "Refund wale user ke message ko "
                    "reply karke sirf refund amount bhejo.\n\n"

                    "Example:\n"
                    "<code>80</code>\n\n"

                    "⚠️ <code>.split</code> dobara likhne "
                    "ki zaroorat nahi hai."
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

        refund_user = get_deal_user(
            active_deal,
            replied_user_id
        )

        if not refund_user:

            bot.reply_to(
                message,
                (
                    "⚠️ Jis user ke message ko "
                    "reply kiya hai, wo current deal "
                    "ka part nahi hai."
                )
            )

            return

        refund_user_id = replied_user_id

        # ======================================================
        # SAME USER
        # ======================================================

        if refund_user_id == data["release_user_id"]:

            bot.reply_to(
                message,
                "⚠️ Release aur refund user same nahi ho sakte."
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

            deal_id=data["deal_id"],

            refund_user_id=refund_user_id,

            refund_amount=amount,

            release_user_id=data["release_user_id"],

            release_amount=data["release_amount"]
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

        # ======================================================
        # TOTAL
        # ======================================================

        release_amount = data["release_amount"]
        refund_amount = amount

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
        # PAYMENT
        # ======================================================

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

        # ======================================================
        # PIN
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
        # SPLIT INFO
        # ======================================================

        bot.send_message(
            group_id,
            (
                "✂️ <b>SPLIT COMPLETED</b>\n\n"

                f"💸 <b>Release:</b> "
                f"{release_mention} — {release_text}\n"

                f"↩️ <b>Refund:</b> "
                f"{refund_mention} — {refund_text}\n\n"

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
        # DELETE AMOUNT MESSAGE
        # ======================================================

        delete_command_message(
            bot,
            message
        )
