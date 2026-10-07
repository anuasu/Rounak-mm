import telebot

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

    if not text:
        return None, None

    raw = text.strip()

    currency = "₹"

    if raw.startswith("$"):

        currency = "$"
        raw = raw[1:].strip()

    elif raw.startswith("₹"):

        currency = "₹"
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

    # IMPORTANT:
    # sqlite3.Row does NOT support .get()
    # So direct [] access is used.

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

    if not message.from_user:

        return False

    return message.from_user.id in MM_CHAT_IDS


# ==========================================================
# GET REPLIED USER
# ==========================================================

def get_replied_user(message):

    if not message.reply_to_message:

        return None

    replied_message = message.reply_to_message

    replied_user = replied_message.from_user

    if not replied_user:

        return None

    if replied_user.is_bot:

        return None

    return replied_user


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

        # ------------------------------------------------------
        # MM ONLY
        # ------------------------------------------------------

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

        # ------------------------------------------------------
        # SQLITE ROW SAFE DEAL ID
        # ------------------------------------------------------

        active_deal_id = active_deal["deal_id"]

        # ------------------------------------------------------
        # OLD / EXISTING STATE
        # ------------------------------------------------------

        old_data = pending_split.get(
            group_id
        )

        if old_data:

            old_deal_id = old_data.get(
                "deal_id"
            )

            # Same deal already running
            if old_deal_id == active_deal_id:

                bot.reply_to(
                    message,
                    (
                        "⚠️ <b>Split already setup hai.</b>\n\n"
                        "Ab <code>.split</code> dobara mat likho.\n\n"
                        "Release ke liye:\n"
                        "<code>.r AMOUNT</code>\n\n"
                        "Refund ke liye:\n"
                        "<code>.f AMOUNT</code>"
                    ),
                    parse_mode="HTML"
                )

                delete_command_message(
                    bot,
                    message
                )

                return

            # Different/old deal
            pending_split.pop(
                group_id,
                None
            )

        # ------------------------------------------------------
        # CREATE NEW STATE
        # ------------------------------------------------------

        pending_split[group_id] = {

            "deal_id": active_deal_id,

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
# HANDLE .R / .F
# ==========================================================

def register_split_input(bot):

    @bot.message_handler(
        func=lambda message: (
            message.chat.type in (
                "group",
                "supergroup"
            )
            and message.text
            and normalize_command(
                message.text
            ).strip().lower().startswith(
                (".r", ".f")
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

        # ======================================================
        # GET STATE
        # ======================================================

        data = pending_split.get(
            group_id
        )

        if not data:

            # No active split
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
                "⚠️ Is group mein active deal nahi hai."
            )

            return

        # ======================================================
        # IMPORTANT SQLITE FIX
        # ======================================================
        #
        # NEVER:
        #
        # active_deal.get("deal_id")
        #
        # sqlite3.Row does not have .get()
        #
        # Use:
        #
        # active_deal["deal_id"]
        #

        active_deal_id = active_deal["deal_id"]

        if data.get("deal_id") != active_deal_id:

            pending_split.pop(
                group_id,
                None
            )

            bot.reply_to(
                message,
                (
                    "⚠️ Current deal change ho gaya hai.\n"
                    "Please <code>.split</code> dobara run karo."
                ),
                parse_mode="HTML"
            )

            return

        # ======================================================
        # PARSE COMMAND
        # ======================================================

        command_text = normalize_command(
            message.text
        ).strip()

        parts = command_text.split()

        if not parts:

            return

        command = parts[0].lower()

        # ======================================================
        # ONLY .R / .F
        # ======================================================

        if command not in (
            ".r",
            ".f"
        ):

            return

        # ======================================================
        # AMOUNT REQUIRED
        # ======================================================

        if len(parts) != 2:

            if command == ".r":

                bot.reply_to(
                    message,
                    (
                        "⚠️ Correct format:\n"
                        "<code>.r 80</code>\n\n"
                        "User ke message ko reply karke bhejo."
                    ),
                    parse_mode="HTML"
                )

            else:

                bot.reply_to(
                    message,
                    (
                        "⚠️ Correct format:\n"
                        "<code>.f 120</code>\n\n"
                        "User ke message ko reply karke bhejo."
                    ),
                    parse_mode="HTML"
                )

            return

        # ======================================================
        # MUST REPLY TO USER
        # ======================================================

        replied_user = get_replied_user(
            message
        )

        if not replied_user:

            bot.reply_to(
                message,
                (
                    "⚠️ <b>User ke message ko reply karo.</b>\n\n"
                    "Example:\n"
                    "<code>.r 80</code>"
                ),
                parse_mode="HTML"
            )

            return

        replied_user_id = replied_user.id

        # ======================================================
        # PARSE AMOUNT
        # ======================================================

        amount, currency = parse_amount(
            parts[1]
        )

        if amount is None:

            bot.reply_to(
                message,
                (
                    "⚠️ Invalid amount.\n\n"
                    "Example:\n"
                    "<code>.r 80</code>"
                ),
                parse_mode="HTML"
            )

            return

        # ======================================================
        # RELEASE
        # ======================================================

        if command == ".r":

            # --------------------------------------------------
            # MUST BE RELEASE STEP
            # --------------------------------------------------

            if data.get("step") != "release":

                bot.reply_to(
                    message,
                    (
                        "⚠️ Release already received.\n\n"
                        "Ab refund user ke message ko reply karke:\n"
                        "<code>.f AMOUNT</code> bhejo."
                    ),
                    parse_mode="HTML"
                )

                return

            # --------------------------------------------------
            # CHECK RELEASE USER
            # --------------------------------------------------

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

            # --------------------------------------------------
            # RELEASE NAME
            # --------------------------------------------------

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
                    active_deal_id,

                "release_user_id":
                    replied_user_id,

                "release_user_name":
                    release_name,

                "release_amount":
                    amount,

                "release_currency":
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

                    "💸 Refund wale user ke message ko "
                    "reply karke:\n\n"

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
        # REFUND
        # ======================================================

        if command == ".f":

            # --------------------------------------------------
            # MUST BE REFUND STEP
            # --------------------------------------------------

            if data.get("step") != "refund":

                bot.reply_to(
                    message,
                    (
                        "⚠️ Pehle release amount submit karo:\n"
                        "<code>.r AMOUNT</code>"
                    ),
                    parse_mode="HTML"
                )

                return

            # --------------------------------------------------
            # CHECK REFUND USER
            # --------------------------------------------------

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

            refund_user_id = replied_user_id

            # --------------------------------------------------
            # SAME USER CHECK
            # --------------------------------------------------

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

            # --------------------------------------------------
            # REFUND NAME
            # --------------------------------------------------

            refund_name = (
                refund_user["first_name"]
                or replied_user.first_name
                or "User"
            )

            # --------------------------------------------------
            # RECORD SPLIT
            # --------------------------------------------------

            success = record_split(

                deal_id=data["deal_id"],

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

                bot.reply_to(
                    message,
                    (
                        "❌ <b>Split complete nahi ho saka.</b>\n\n"
                        "Deal already completed ho sakti hai "
                        "ya database update fail hua hai."
                    ),
                    parse_mode="HTML"
                )

                pending_split.pop(
                    group_id,
                    None
                )

                return

            # ==================================================
            # TOTAL VOUCHER AMOUNT
            # ==================================================

            release_amount = data[
                "release_amount"
            ]

            refund_amount = amount

            total_amount = (
                release_amount
                + refund_amount
            )

            # ==================================================
            # CURRENCY
            # ==================================================

            release_currency = data.get(
                "release_currency",
                "₹"
            )

            final_currency = (
                currency
                if currency != "₹"
                else release_currency
            )

            # ==================================================
            # FORMAT
            # ==================================================

            release_text = format_amount(
                release_amount,
                release_currency
            )

            refund_text = format_amount(
                refund_amount,
                currency
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
            # PIN PAYMENT
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
            # VOUCHER TEXT
            # ==================================================

            try:

                bot.send_message(
                    group_id,
                    (
                        f"<code>I vouch @RounakMM "
                        f"for MMD payment "
                        f"{total_text}</code>"
                    ),
                    parse_mode="HTML"
                )

            except Exception as error:

                print(
                    f"Split voucher message error: {error}"
                )

            # ==================================================
            # VOUCHER REQUEST
            # ==================================================

            try:

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

            except Exception as error:

                print(
                    f"Split voucher request error: {error}"
                )

            # ==================================================
            # SPLIT INFORMATION
            # ==================================================

            try:

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

            except Exception as error:

                print(
                    f"Split completion message error: {error}"
                )

            # ==================================================
            # DELETE .F MESSAGE
            # ==================================================

            delete_command_message(
                bot,
                message
            )

            return
