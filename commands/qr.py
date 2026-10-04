from config import MM_CHAT_IDS, ADMIN_IDS

from database.database import (
    get_active_deal,
    get_qr,
    set_qr
)


# ==========================================
# FEE CALCULATOR
# ==========================================

def calculate_mm_fee(amount):

    if 10 <= amount <= 49:
        return 10

    elif 50 <= amount <= 349:
        return 20

    elif 350 <= amount <= 499:
        return 30

    elif 500 <= amount <= 699:
        return 40

    elif 700 <= amount <= 999:
        return 50

    elif 1000 <= amount <= 1499:
        return 80

    elif 1500 <= amount <= 1999:
        return 100

    elif 2000 <= amount <= 2499:
        return 130

    elif 2500 <= amount <= 2999:
        return 160

    elif amount >= 3000:
    # 3000+ ke liye next slabs
        extra_slabs = int((amount - 3000) // 500)
        return 190 + (extra_slabs * 30)

    return None


# ==========================================
# USER MENTION
# ==========================================

def user_mention(user_id, name):

    name = name or "User"

    return (
        f'<a href="tg://user?id={user_id}">'
        f'{name}'
        f'</a>'
    )


# ==========================================
# REGISTER QR
# ==========================================

def register_qr(bot):

    # ======================================
    # /setqr 1 ... /setqr 10
    # ======================================

    @bot.message_handler(
        commands=["setqr"]
    )
    def set_qr_command(message):

        # ----------------------------------
        # MM / ADMIN ONLY
        # ----------------------------------

        if (
            message.from_user.id not in MM_CHAT_IDS
            and
            message.from_user.id not in ADMIN_IDS
        ):
            return

        # ----------------------------------
        # CHECK QR NUMBER
        # ----------------------------------

        parts = message.text.strip().split()

        if len(parts) != 2:

            bot.reply_to(
                message,
                (
                    "⚠️ QR number do.\n\n"
                    "Example:\n"
                    "<code>/setqr 1</code>\n"
                    "<code>/setqr 2</code>\n\n"
                    "QR 1 se QR 10 tak allowed hai."
                ),
                parse_mode="HTML"
            )

            return

        try:
            qr_number = int(parts[1])

        except ValueError:

            bot.reply_to(
                message,
                "⚠️ QR number valid hona chahiye."
            )

            return

        if qr_number < 1 or qr_number > 10:

            bot.reply_to(
                message,
                "⚠️ Sirf QR 1 se QR 10 tak set kar sakte ho."
            )

            return

        # ----------------------------------
        # PHOTO REPLY REQUIRED
        # ----------------------------------

        if not message.reply_to_message:

            bot.reply_to(
                message,
                (
                    f"⚠️ QR {qr_number} ki image ko "
                    f"reply karke <code>/setqr {qr_number}</code> bhejo."
                ),
                parse_mode="HTML"
            )

            return

        replied = message.reply_to_message

        if not replied.photo:

            bot.reply_to(
                message,
                "⚠️ Reply kiya hua message photo hona chahiye."
            )

            return

        # ----------------------------------
        # GET TELEGRAM FILE ID
        # ----------------------------------

        image_file_id = replied.photo[-1].file_id

        # ----------------------------------
        # SAVE QR
        # ----------------------------------

        set_qr(
            qr_number,
            image_file_id
        )

        bot.reply_to(
            message,
            (
                f"✅ <b>QR {qr_number} Updated!</b>\n\n"
                f"Ab <code>.qr{qr_number} amount</code> "
                "use kar sakte ho."
            ),
            parse_mode="HTML"
        )


    # ======================================
    # .qr1 ... .qr10
    # ======================================

    @bot.message_handler(
        func=lambda message:
        message.text
        and message.text.strip().lower().startswith(".qr")
    )
    def qr_payment_command(message):

        # ----------------------------------
        # MM ONLY
        # ----------------------------------

        if message.from_user.id not in MM_CHAT_IDS:

            if message.from_user.id in ADMIN_IDS:

                bot.reply_to(
                    message,
                    "⚠️ Sirf MM ye command use kar sakta hai."
                )

            return

        # ----------------------------------
        # GROUP ONLY
        # ----------------------------------

        if message.chat.type not in [
            "group",
            "supergroup"
        ]:
            return

        # ----------------------------------
        # COMMAND
        # ----------------------------------

        parts = message.text.strip().split()

        command = parts[0].lower()

        try:
            qr_number = int(command.replace(".qr", ""))

        except ValueError:
            return

        if qr_number < 1 or qr_number > 10:
            return

        # ----------------------------------
        # AMOUNT
        # ----------------------------------

        if len(parts) != 2:

            bot.reply_to(
                message,
                (
                    f"⚠️ Amount do.\n\n"
                    f"Example:\n"
                    f"<code>.qr{qr_number} 500</code>"
                ),
                parse_mode="HTML"
            )

            return

        raw_amount = parts[1].replace("₹", "").strip()

        try:
            amount = float(raw_amount)

        except ValueError:

            bot.reply_to(
                message,
                "⚠️ Amount valid number hona chahiye."
            )

            return

        if amount < 10:

            bot.reply_to(
                message,
                "⚠️ Minimum amount ₹10 hai."
            )

            return

        # ----------------------------------
        # CALCULATE FEE
        # ----------------------------------

        fee = calculate_mm_fee(amount)

        if fee is None:

            bot.reply_to(
                message,
                "⚠️ Is amount ke liye MM fee set nahi hai."
            )

            return

        total = amount + fee

        # ----------------------------------
        # GET ACTIVE DEAL
        # ----------------------------------

        active_deal = get_active_deal(
            message.chat.id
        )

        if not active_deal:

            bot.reply_to(
                message,
                "⚠️ Is group mein koi active deal nahi hai."
            )

            return

        # ----------------------------------
        # GET QR IMAGE
        # ----------------------------------

        image_file_id = get_qr(
            qr_number
        )

        if not image_file_id:

            bot.reply_to(
                message,
                (
                    f"⚠️ QR {qr_number} abhi set nahi hai.\n\n"
                    f"Pehle QR image ko reply karke "
                    f"<code>/setqr {qr_number}</code> bhejo."
                ),
                parse_mode="HTML"
            )

            return

        # ----------------------------------
        # GET DEAL USERS
        # ----------------------------------

        user_1_id = active_deal["user_1_id"]
        user_2_id = active_deal["user_2_id"]

        try:

            user_1 = bot.get_chat(user_1_id)
            user_2 = bot.get_chat(user_2_id)

            user_1_name = user_1.first_name or "User 1"
            user_2_name = user_2.first_name or "User 2"

        except Exception as error:

            print(
                f"QR user lookup error: {error}"
            )

            user_1_name = "User 1"
            user_2_name = "User 2"

        mention_1 = user_mention(
            user_1_id,
            user_1_name
        )

        mention_2 = user_mention(
            user_2_id,
            user_2_name
        )

        # ----------------------------------
        # FORMAT AMOUNT
        # ----------------------------------

        amount_text = f"₹{amount:g}"
        fee_text = f"₹{fee:g}"
        total_text = f"₹{total:g}"

        # ----------------------------------
        # QR CAPTION
        # ----------------------------------

        caption = (
            f"💳 <b>This is QR {qr_number}</b>\n\n"
            f"Please pay <b>{total_text}</b> on this QR.\n\n"
            f"💰 Amount: {amount_text}\n"
            f"💸 MM Fee: {fee_text}\n"
            f"💳 Total: <b>{total_text}</b>\n\n"
            f"👤 {mention_1}\n"
            f"👤 {mention_2}"
        )

        # ----------------------------------
        # SEND QR
        # ----------------------------------

        bot.send_photo(
            message.chat.id,
            image_file_id,
            caption=caption,
            parse_mode="HTML"
  )
