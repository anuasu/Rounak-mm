from config import MM_CHAT_IDS, ADMIN_IDS

from database.database import (
    get_active_deal,
    finalize_deal,
    get_user,
    save_user
)

from commands.command_utils import (
    normalize_command,
    delete_command_message
)


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
# GET REPLIED USER
# ==========================================

def get_replied_user(message):

    if not message.reply_to_message:
        return None

    replied_message = message.reply_to_message

    if not replied_message.from_user:
        return None

    return replied_message.from_user


# ==========================================
# CHECK USER IN CURRENT DEAL
# ==========================================

def is_deal_user(active_deal, user_id):

    return user_id in (
        active_deal["user_1_id"],
        active_deal["user_2_id"]
    )


# ==========================================
# REGISTER RELEASE
# ==========================================

def register_release(bot):

    @bot.message_handler(
        func=lambda message:
        message.text
        and normalize_command(message.text)
        .lower()
        .startswith(".release")
    )
    def release_command(message):

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
        # ACTIVE DEAL
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
        # MUST REPLY
        # ==================================

        replied_user = get_replied_user(message)

        if not replied_user:

            bot.reply_to(
                message,
                (
                    "⚠️ Release ke liye deal user ke "
                    "message par reply karo.\n\n"
                    "Use:\n"
                    "<code>Reply to user → .release AMOUNT</code>\n\n"
                    "Example:\n"
                    "<code>.release 500</code>"
                ),
                parse_mode="HTML"
            )

            delete_command_message(
                bot,
                message
            )

            return

        # ==================================
        # CHECK REPLIED USER
        # ==================================

        release_user_id = replied_user.id

        if not is_deal_user(
            active_deal,
            release_user_id
        ):

            bot.reply_to(
                message,
                (
                    "⚠️ Jis user ke message par reply "
                    "kiya hai wo current deal ka user nahi hai."
                )
            )

            delete_command_message(
                bot,
                message
            )

            return

        # ==================================
        # COMMAND
        #
        # .release AMOUNT
        #
        # Example:
        # .release 500
        # .release ₹500
        # .release $500
        # ==================================

        command_text = normalize_command(
            message.text
        )

        parts = command_text.split()

        if len(parts) != 2:

            bot.reply_to(
                message,
                (
                    "⚠️ Release format galat hai.\n\n"
                    "Deal user ke message par reply karke:\n"
                    "<code>.release AMOUNT</code>\n\n"
                    "Example:\n"
                    "<code>.release 500</code>"
                ),
                parse_mode="HTML"
            )

            delete_command_message(
                bot,
                message
            )

            return

        # ==================================
        # AMOUNT
        # ==================================

        raw_amount = parts[1].strip()

        currency = "₹"

        if raw_amount.startswith("$"):

            currency = "$"
            raw_amount = raw_amount[1:]

        elif raw_amount.startswith("₹"):

            raw_amount = raw_amount[1:]

        try:

            release_amount = float(
                raw_amount
            )

        except (ValueError, TypeError):

            bot.reply_to(
                message,
                "⚠️ Amount valid number hona chahiye."
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

        # ==================================
        # GET OTHER USER
        # ==================================

        user_1_id = active_deal["user_1_id"]
        user_2_id = active_deal["user_2_id"]

        if release_user_id == user_1_id:

            other_user_id = user_2_id

        else:

            other_user_id = user_1_id

        # ==================================
        # GET USER DATA
        # ==================================

        release_user = get_user(
            release_user_id
        )

        other_user = get_user(
            other_user_id
        )

        # ==================================
        # SAVE / UPDATE USERS
        # ==================================

        try:

            release_chat = bot.get_chat(
                release_user_id
            )

            other_chat = bot.get_chat(
                other_user_id
            )

            release_name = (
                release_chat.first_name
                or (
                    release_user["first_name"]
                    if release_user
                    else ""
                )
                or "User"
            )

            other_name = (
                other_chat.first_name
                or (
                    other_user["first_name"]
                    if other_user
                    else ""
                )
                or "User"
            )

            save_user(
                release_user_id,
                release_name,
                release_chat.username
                or (
                    release_user["username"]
                    if release_user
                    else ""
                )
                or ""
            )

            save_user(
                other_user_id,
                other_name,
                other_chat.username
                or (
                    other_user["username"]
                    if other_user
                    else ""
                )
                or ""
            )

        except Exception as error:

            print(
                f"Release user lookup error: {error}"
            )

            release_name = (
                release_user["first_name"]
                if release_user
                else ""
            ) or replied_user.first_name or "User"

            other_name = (
                other_user["first_name"]
                if other_user
                else ""
            ) or "User"

        # ==================================
        # FINALIZE DEAL
        #
        # IMPORTANT:
        # Release amount goes ONLY to
        # the replied user.
        #
        # Other user gets 0 here.
        # ==================================

        success = finalize_deal(
            active_deal["deal_id"],
            "release",
            {
                user_1_id: (
                    release_amount
                    if release_user_id == user_1_id
                    else 0
                ),

                user_2_id: (
                    release_amount
                    if release_user_id == user_2_id
                    else 0
                )
            }
        )

        # ==================================
        # FAILED
        # ==================================

        if not success:

            bot.reply_to(
                message,
                (
                    "❌ Release complete nahi ho saka.\n\n"
                    "Possible reason:\n"
                    "• Deal already completed ho sakti hai.\n"
                    "• Amount available amount se zyada ho sakta hai."
                )
            )

            delete_command_message(
                bot,
                message
            )

            return

        # ==================================
        # MENTIONS
        # ==================================

        release_mention = user_mention(
            release_user_id,
            release_name
        )

        other_mention = user_mention(
            other_user_id,
            other_name
        )

        amount_text = (
            f"{currency}{release_amount:g}"
        )

        # ==================================
        # PAYMENT SENT
        # ==================================

        payment_message = bot.send_message(
            message.chat.id,
            (
                "💸 <b>PAYMENT SENT</b>\n\n"
                f"{amount_text} sent to "
                f"{release_mention}.\n\n"
                "Please drop voucher."
            ),
            parse_mode="HTML"
        )

        # ==================================
        # PIN PAYMENT
        # ==================================

        try:

            bot.pin_chat_message(
                message.chat.id,
                payment_message.message_id,
                disable_notification=True
            )

        except Exception as error:

            print(
                f"Release pin error: {error}"
            )

        # ==================================
        # VOUCHER
        # ==================================

        bot.send_message(
            message.chat.id,
            (
                f"<code>I vouch @RounakMM "
                f"for MM'D {amount_text}</code>"
            ),
            parse_mode="HTML"
        )

        # ==================================
        # BOTH USERS
        # ==================================

        bot.send_message(
            message.chat.id,
            (
                f"{release_mention} {other_mention}\n\n"
                f"📩 <b>Please drop voucher "
                f"for {amount_text}.</b>"
            ),
            parse_mode="HTML"
        )

        # ==================================
        # RELEASE INFO
        # ==================================

        bot.send_message(
            message.chat.id,
            (
                "✅ <b>DEAL RELEASED</b>\n\n"
                f"🤝 Deal: <b>#{active_deal['deal_id']}</b>\n"
                f"👤 Released To: {release_mention}\n"
                f"💰 Amount: <b>{amount_text}</b>\n"
                "🕐 Release recorded successfully.\n\n"
                "📊 Leaderboard updated."
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
