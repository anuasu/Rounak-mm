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
# CLEAN USERNAME
# ==========================================

def clean_username(username):

    username = username.strip()

    if username.startswith("@"):
        username = username[1:]

    return username.lower()


# ==========================================
# FIND USER FROM CURRENT DEAL
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
        # COMMAND
        #
        # .release @username AMOUNT
        #
        # Example:
        # .release @abc 500
        # ==================================

        command_text = normalize_command(
            message.text
        )

        parts = command_text.split()

        if len(parts) != 3:

            bot.reply_to(
                message,
                (
                    "⚠️ Release format galat hai.\n\n"
                    "Use:\n"
                    "<code>.release @username AMOUNT</code>\n\n"
                    "Example:\n"
                    "<code>.release @abc 500</code>"
                ),
                parse_mode="HTML"
            )

            delete_command_message(
                bot,
                message
            )

            return

        # ==================================
        # USERNAME
        # ==================================

        username = parts[1]

        # ==================================
        # AMOUNT
        # ==================================

        raw_amount = parts[2].strip()

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
                    "Example:\n"
                    "<code>.release @username 500</code>"
                ),
                parse_mode="HTML"
            )

            delete_command_message(
                bot,
                message
            )

            return

        # ==================================
        # AUTOMATIC CHAT ID
        # ==================================

        release_user_id = release_user["chat_id"]

        user_1_id = active_deal["user_1_id"]
        user_2_id = active_deal["user_2_id"]

        # ==================================
        # OTHER USER
        # ==================================

        if release_user_id == user_1_id:

            other_user_id = user_2_id

        else:

            other_user_id = user_1_id

        # ==================================
        # SAVE / UPDATE USER DATA
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
                or release_user["first_name"]
                or "User"
            )

            other_name = (
                other_chat.first_name
                or "User"
            )

            save_user(
                release_user_id,
                release_name,
                release_chat.username
                or release_user["username"]
                or ""
            )

            save_user(
                other_user_id,
                other_name,
                other_chat.username
                or ""
            )

        except Exception as error:

            print(
                f"Release user lookup error: {error}"
            )

            release_name = (
                release_user["first_name"]
                or "User"
            )

            other_name = "User"

        # ==================================
        # FINALIZE DEAL
        #
        # BOTH users:
        # +1 deal
        # SAME amount
        # ==================================

        success = finalize_deal(
            active_deal["deal_id"],
            "release",
            {
                user_1_id: release_amount,
                user_2_id: release_amount
            }
        )

        if not success:

            bot.reply_to(
                message,
                "❌ Release process complete nahi ho saka."
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
                f"🕐 Release recorded successfully.\n\n"
                "📊 Leaderboard updated for both users."
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
