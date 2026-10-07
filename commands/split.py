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
# PARSE AMOUNT
# ==========================================================

def parse_amount(text):

    if text is None:
        return None, None

    raw = str(text).strip()

    if not raw:
        return None, None

    currency = "₹"

    if raw.startswith("$"):

        currency = "$"
        raw = raw[1:].strip()

    elif raw.startswith("₹"):

        raw = raw[1:].strip()

    # Remove commas
    raw = raw.replace(",", "")

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

    try:
        return f"{currency}{float(amount):g}"
    except Exception:
        return f"{currency}{amount}"


# ==========================================================
# CHECK MM
# ==========================================================

def is_mm(message):

    try:

        return (
            message.from_user
            and message.from_user.id in MM_CHAT_IDS
        )

    except Exception:

        return False


# ==========================================================
# GET USER FROM ACTIVE DEAL
# ==========================================================

def get_deal_user(active_deal, user_id):

    if not active_deal:
        return None

    try:

        user_1_id = active_deal["user_1_id"]
        user_2_id = active_deal["user_2_id"]

    except Exception:

        return None

    if user_id == user_1_id:

        return get_user(user_1_id)

    if user_id == user_2_id:

        return get_user(user_2_id)

    return None


# ==========================================================
# GET DEAL USER NAME
# ==========================================================

def get_user_name(db_user, telegram_user):

    if db_user:

        name = (
            db_user["first_name"]
            if db_user["first_name"]
            else None
        )

        if name:
            return name

    if telegram_user:

        return (
            telegram_user.first_name
            or "User"
        )

    return "User"


# ==========================================================
# SEND ERROR
# ==========================================================

def split_error(bot, message, text):

    try:

        bot.reply_to(
            message,
            text,
            parse_mode="HTML"
        )

    except Exception as error:

        print(
            f"[SPLIT] Error message failed: {error}"
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

        print(
            f"[SPLIT] .split received | "
            f"chat={getattr(message.chat, 'id', None)} | "
            f"user={getattr(message.from_user, 'id', None)}"
        )

        # ==================================================
        # MM ONLY
        # ==================================================

        if not is_mm(message):

            if (
                message.from_user
                and message.from_user.id in ADMIN_IDS
            ):

                split_error(
                    bot,
                    message,
                    "⚠️ Sirf MM ye command use kar sakta hai."
                )

            return

        # ==================================================
        # GROUP ONLY
        # ==================================================

        if message.chat.type not in (
            "group",
            "supergroup"
        ):

            split_error(
                bot,
                message,
                "⚠️ <code>.split</code> sirf group mein use kar sakte ho."
            )

            return

        group_id = message.chat.id

        # ==================================================
        # ACTIVE DEAL
        # ==================================================

        active_deal = get_active_deal(
            group_id
        )

        if not active_deal:

            split_error(
                bot,
                message,
                "⚠️ Is group mein koi active deal nahi hai."
            )

            delete_command_message(
                bot,
                message
            )

            return

        deal_id = active_deal["deal_id"]

        # ==================================================
        # OLD STATE CHECK
        # ==================================================

        old_state = pending_split.get(
            group_id
        )

        if old_state:

            old_deal_id = old_state.get(
                "deal_id"
            )

            # ----------------------------------------------
            # OLD DEAL
            # ----------------------------------------------

            if old_deal_id != deal_id:

                print(
                    f"[SPLIT] Removing stale state | "
                    f"group={group_id}"
                )

                pending_split.pop(
                    group_id,
                    None
                )

            # ----------------------------------------------
            # SAME DEAL
            # ----------------------------------------------

            else:

                step = old_state.get(
                    "step",
                    "release"
                )

                if step == "release":

                    next_text = (
                        "💸 Release wale user ke "
                        "message ko reply karke "
                        "<b>sirf amount</b> bhejo."
                    )

                else:

                    next_text = (
                        "↩️ Refund wale user ke "
                        "message ko reply karke "
                        "<b>sirf amount</b> bhejo."
                    )

                split_error(
                    bot,
                    message,
                    (
                        "⚠️ <b>Split already setup hai.</b>\n\n"
                        f"{next_text}\n\n"
                        "Example:\n"
                        "<code>80</code>\n\n"
                        "⚠️ <code>.split</code> dobara "
                        "likhne ki zaroorat nahi hai."
                    )
                )

                delete_command_message(
                    bot,
                    message
                )

                return

        # ==================================================
        # CREATE NEW SPLIT STATE
        # ==================================================

        pending_split[group_id] = {

            "deal_id": deal_id,

            "step": "release"

        }

        print(
            f"[SPLIT] Started | "
            f"group={group_id} | "
            f"deal={deal_id}"
        )

        # ==================================================
        # ASK RELEASE
        # ==================================================

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
# HANDLE SPLIT REPLY
# ==========================================================

def register_split_input(bot):

    @bot.message_handler(
        func=lambda message: (
            message.chat
            and message.chat.type in (
                "group",
                "supergroup"
            )
            and message.chat.id in pending_split
            and message.text is not None
            and message.reply_to_message is not None
        ),
        content_types=["text"]
    )
    def split_reply_handler(message):

        print(
            f"[SPLIT] REPLY RECEIVED | "
            f"chat={getattr(message.chat, 'id', None)} | "
            f"user={getattr(message.from_user, 'id', None)} | "
            f"text={repr(message.text)}"
        )

        # ==================================================
        # MM CHECK
        # ==================================================

        if not is_mm(message):

            print(
                "[SPLIT] Reply ignored: sender is not MM"
            )

            return

        group_id = message.chat.id

        # ==================================================
        # GET STATE
        # ==================================================

        data = pending_split.get(
            group_id
        )

        if not data:

            print(
                "[SPLIT] Reply ignored: no pending state"
            )

            return

        print(
            f"[SPLIT] Current state: {data}"
        )

        # ==================================================
        # ACTIVE DEAL
        # ==================================================

        active_deal = get_active_deal(
            group_id
        )

        if not active_deal:

            print(
                "[SPLIT] Active deal disappeared"
            )

            pending_split.pop(
                group_id,
                None
            )

            split_error(
                bot,
                message,
                "⚠️ Active deal nahi mila. Split reset kar diya gaya."
            )

            return

        # ==================================================
        # DEAL ID CHECK
        # ==================================================

        if (
            data.get("deal_id")
            != active_deal.get("deal_id")
        ):

            print(
                "[SPLIT] Deal ID mismatch"
            )

            pending_split.pop(
                group_id,
                None
            )

            split_error(
                bot,
                message,
                "⚠️ Active deal change ho gaya. Split reset kar diya gaya."
            )

            return

        # ==================================================
        # REPLY CHECK
        # ==================================================

        if not message.reply_to_message:

            print(
                "[SPLIT] No reply_to_message"
            )

            split_error(
                bot,
                message,
                (
                    "⚠️ Amount <b>reply karke</b> bhejo.\n\n"
                    "Example:\n"
                    "<code>80</code>"
                )
            )

            return

        # ==================================================
        # GET REPLIED MESSAGE USER
        # ==================================================

        replied_message = (
            message.reply_to_message
        )

        replied_user = (
            replied_message.from_user
        )

        if not replied_user:

            print(
                "[SPLIT] Reply has no from_user"
            )

            split_error(
                bot,
                message,
                "⚠️ Replied message ka user identify nahi ho saka."
            )

            return

        # ==================================================
        # BOT CHECK
        # ==================================================

        if replied_user.is_bot:

            split_error(
                bot,
                message,
                "⚠️ Bot ke message ko reply mat karo. Deal user ke message ko reply karo."
            )

            return

        replied_user_id = (
            replied_user.id
        )

        print(
            f"[SPLIT] Replied user = {replied_user_id}"
        )

        # ==================================================
        # PARSE AMOUNT
        # ==================================================

        amount, currency = parse_amount(
            message.text
        )

        if amount is None:

            print(
                f"[SPLIT] Invalid amount: {repr(message.text)}"
            )

            split_error(
                bot,
                message,
                (
                    "⚠️ Sirf valid amount bhejo.\n\n"
                    "Example:\n"
                    "<code>120</code>\n\n"
                    "₹120 bhi allowed hai."
                )
            )

            return

        print(
            f"[SPLIT] Parsed amount={amount}, "
            f"currency={currency}"
        )

        # ==================================================
        # CURRENT STEP
        # ==================================================

        step = data.get(
            "step"
        )

        # ==================================================
        # RELEASE STEP
        # ==================================================

        if step == "release":

            print(
                "[SPLIT] Processing RELEASE step"
            )

            release_user = get_deal_user(
                active_deal,
                replied_user_id
            )

            if not release_user:

                print(
                    f"[SPLIT] Release user not in deal: "
                    f"{replied_user_id}"
                )

                split_error(
                    bot,
                    message,
                    (
                        "⚠️ Jis user ke message ko "
                        "reply kiya hai, wo current "
                        "deal ka part nahi hai."
                    )
                )

                return

            release_name = get_user_name(
                release_user,
                replied_user
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

            print(
                f"[SPLIT] RELEASE SAVED | "
                f"user={replied_user_id} | "
                f"amount={amount}"
            )

            # --------------------------------------------------
            # ASK REFUND
            # --------------------------------------------------

            bot.send_message(
                group_id,
                (
                    "↩️ <b>NOW REFUND USER</b>\n\n"

                    "Refund wale user ke message ko "
                    "reply karke <b>sirf refund amount</b> bhejo.\n\n"

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

        # ==================================================
        # REFUND STEP
        # ==================================================

        if step == "refund":

            print(
                "[SPLIT] Processing REFUND step"
            )

            refund_user = get_deal_user(
                active_deal,
                replied_user_id
            )

            if not refund_user:

                print(
                    f"[SPLIT] Refund user not in deal: "
                    f"{replied_user_id}"
                )

                split_error(
                    bot,
                    message,
                    (
                        "⚠️ Jis user ke message ko "
                        "reply kiya hai, wo current "
                        "deal ka part nahi hai."
                    )
                )

                return

            refund_user_id = (
                replied_user_id
            )

            # ==================================================
            # SAME USER
            # ==================================================

            if (
                refund_user_id
                == data["release_user_id"]
            ):

                split_error(
                    bot,
                    message,
                    (
                        "⚠️ Release aur refund user "
                        "same nahi ho sakte.\n\n"
                        "Dusre deal user ke message ko "
                        "reply karo."
                    )
                )

                return

            refund_name = get_user_name(
                refund_user,
                replied_user
            )

            # ==================================================
            # RECORD SPLIT
            # ==================================================

            print(
                f"[SPLIT] Recording split | "
                f"deal={data['deal_id']} | "
                f"release={data['release_amount']} | "
                f"refund={amount}"
            )

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

            if not success:

                print(
                    "[SPLIT] record_split returned False"
                )

                pending_split.pop(
                    group_id,
                    None
                )

                split_error(
                    bot,
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

            refund_amount = amount

            total_amount = (
                release_amount
                + refund_amount
            )

            final_currency = (
                data.get("currency")
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

            print(
                f"[SPLIT] COMPLETED | "
                f"deal={data['deal_id']} | "
                f"total={total_text}"
            )

            # ==================================================
            # MENTIONS
            # ==================================================

            release_mention = user_mention(
                data["release_user_id"],
                data["release_user_name"]
            )

            refund_mention = user_mention(
                refund_user_id,
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
                    f"[SPLIT] Pin error: {error}"
                )

            # ==================================================
            # VOUCHER
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
            # DELETE AMOUNT MESSAGE
            # ==================================================

            delete_command_message(
                bot,
                message
            )

            return

        # ==================================================
        # UNKNOWN STEP
        # ==================================================

        print(
            f"[SPLIT] Unknown step: {step}"
        )

        pending_split.pop(
            group_id,
            None
        )

        split_error(
            bot,
            message,
            (
                "⚠️ Split state invalid ho gaya.\n"
                "Please <code>.split</code> dobara start karo."
            )
        )
