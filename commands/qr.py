import re

from config import MM_CHAT_IDS, ADMIN_IDS

from database.database import (
    get_active_deal,
    get_qr,
    set_qr,
    set_qr_upi,
    get_qr_upi
)

from telebot import types


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

    @bot.message_handler(commands=["setqr"])
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
        # QR NUMBER
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
        # ASK QR IMAGE
        # ----------------------------------

        bot.reply_to(
            message,
            (
                f"📱 <b>SET QR {qr_number}</b>\n\n"
                "Please share your QR image."
            ),
            parse_mode="HTML"
        )

        # ----------------------------------
        # WAIT FOR PHOTO
        # ----------------------------------

        bot.register_next_step_handler(
            message,
            receive_qr_image,
            qr_number
        )


    # ======================================
    # RECEIVE QR IMAGE
    # ======================================

    def receive_qr_image(message, qr_number):

        if (
            message.from_user.id not in MM_CHAT_IDS
            and
            message.from_user.id not in ADMIN_IDS
        ):
            return

        if not message.photo:

            bot.send_message(
                message.chat.id,
                "⚠️ Please send a QR image."
            )

            bot.register_next_step_handler(
                message,
                receive_qr_image,
                qr_number
            )

            return

        # ----------------------------------
        # GET FILE ID
        # ----------------------------------

        image_file_id = message.photo[-1].file_id

        # ----------------------------------
        # SAVE QR
        # ----------------------------------

        set_qr(
            qr_number,
            image_file_id
        )

        # ----------------------------------
        # ASK UPI
        # ----------------------------------

        markup = types.InlineKeyboardMarkup()

        no_upi_button = types.InlineKeyboardButton(
            "❌ No, I can't add ID",
            callback_data=(
                f"qr_no_upi:"
                f"{qr_number}:"
                f"{message.from_user.id}"
            )
        )

        markup.add(no_upi_button)

        bot.send_message(
            message.chat.id,
            (
                f"✅ <b>QR {qr_number} saved!</b>\n\n"
                "Please share your <b>UPI ID</b>.\n\n"
                "Example:\n"
                "<code>yourname@upi</code>\n\n"
                "Or tap the button below if you don't want "
                "to add a UPI ID."
            ),
            parse_mode="HTML",
            reply_markup=markup
        )

        # ----------------------------------
        # NEXT MESSAGE = UPI
        # ----------------------------------

        bot.register_next_step_handler(
            message,
            receive_upi,
            qr_number
        )


    # ======================================
    # RECEIVE UPI
    # ======================================

    def receive_upi(message, qr_number):

        # ----------------------------------
        # BUTTON / NON TEXT
        # ----------------------------------

        if not message.text:

            bot.send_message(
                message.chat.id,
                "⚠️ Please send your UPI ID as text."
            )

            bot.register_next_step_handler(
                message,
                receive_upi,
                qr_number
            )

            return

        upi_id = message.text.strip()

        # ----------------------------------
        # EMPTY
        # ----------------------------------

        if not upi_id:

            bot.send_message(
                message.chat.id,
                "⚠️ Please send a valid UPI ID."
            )

            bot.register_next_step_handler(
                message,
                receive_upi,
                qr_number
            )

            return

        # ----------------------------------
        # SAVE UPI
        # ----------------------------------

        set_qr_upi(
            qr_number,
            upi_id
        )

        # ----------------------------------
        # SUCCESS
        # ----------------------------------

        bot.send_message(
            message.chat.id,
            (
                f"✅ <b>QR {qr_number} UPDATED</b>\n\n"
                "📱 QR: <b>Saved</b>\n"
                "💳 UPI ID:\n"
                f"<code>{upi_id}</code>\n\n"
                f"Use <code>.qr{qr_number} amount</code> "
                "in your deal."
            ),
            parse_mode="HTML"
        )


    # ======================================
    # NO UPI BUTTON
    # ======================================

    @bot.callback_query_handler(
        func=lambda call:
        call.data.startswith("qr_no_upi:")
    )
    def no_upi_callback(call):

        try:

            parts = call.data.split(":")

            qr_number = int(parts[1])
            owner_id = int(parts[2])

        except Exception:

            bot.answer_callback_query(
                call.id,
                "Invalid request."
            )

            return

        # ----------------------------------
        # OWNER CHECK
        # ----------------------------------

        if call.from_user.id != owner_id:

            bot.answer_callback_query(
                call.id,
                "⚠️ Sirf QR set karne wala user use kar sakta hai."
            )

            return

        # ----------------------------------
        # SAVE NO UPI
        # ----------------------------------

        set_qr_upi(
            qr_number,
            None
        )

        bot.answer_callback_query(
            call.id,
            "No UPI saved."
        )

        # ----------------------------------
        # UPDATE MESSAGE
        # ----------------------------------

        try:

            bot.edit_message_text(
                (
                    f"✅ <b>QR {qr_number} UPDATED</b>\n\n"
                    "📱 QR: <b>Saved</b>\n"
                    "💳 UPI: <b>No UPI added here</b>\n\n"
                    f"Use <code>.qr{qr_number} amount</code> "
                    "in your deal."
                ),
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML"
            )

        except Exception as error:

            print(
                f"QR UPI message edit error: {error}"
            )


    # ======================================
    # .qr1 ... .qr10
    #
    # SUPPORTED:
    #
    # .qr1 500
    # . qr1 500
    # .  qr1 500
    # .   QR1   500
    # .qr10 1000
    #
    # ======================================

    @bot.message_handler(
        func=lambda message:
        message.text
        and re.match(
            r"^\s*\.\s*qr\s*(?:[1-9]|10)\s+",
            message.text,
            re.IGNORECASE
        )
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
        # ORIGINAL TEXT
        # ----------------------------------

        text = message.text.strip()

        # ----------------------------------
        # PARSE COMMAND
        #
        # .qr1 500
        # . qr1 500
        # .  qr1 500
        # .   QR1   500
        # ----------------------------------

        match = re.match(
            r"^\s*\.\s*qr\s*(1|2|3|4|5|6|7|8|9|10)\s+(.+?)\s*$",
            text,
            re.IGNORECASE
        )

        if not match:
            return

        qr_number = int(
            match.group(1)
        )

        raw_amount = match.group(2).strip()

        # ----------------------------------
        # DELETE COMMAND
        # ----------------------------------

        try:

            bot.delete_message(
                message.chat.id,
                message.message_id
            )

        except Exception as error:

            print(
                f"QR command delete error: {error}"
            )

        # ----------------------------------
        # AMOUNT
        # ----------------------------------

        raw_amount = (
            raw_amount
            .replace("₹", "")
            .replace(",", "")
            .strip()
        )

        try:

            amount = float(
                raw_amount
            )

        except ValueError:

            bot.send_message(
                message.chat.id,
                "⚠️ Amount valid number hona chahiye."
            )

            return

        # ----------------------------------
        # MINIMUM AMOUNT
        # ----------------------------------

        if amount < 10:

            bot.send_message(
                message.chat.id,
                "⚠️ Minimum amount ₹10 hai."
            )

            return

        # ----------------------------------
        # CALCULATE FEE
        # ----------------------------------

        fee = calculate_mm_fee(
            amount
        )

        if fee is None:

            bot.send_message(
                message.chat.id,
                "⚠️ Is amount ke liye MM fee set nahi hai."
            )

            return

        total = amount + fee

        # ----------------------------------
        # ACTIVE DEAL
        # ----------------------------------

        active_deal = get_active_deal(
            message.chat.id
        )

        if not active_deal:

            bot.send_message(
                message.chat.id,
                "⚠️ Is group mein koi active deal nahi hai."
            )

            return

        # ----------------------------------
        # QR IMAGE
        # ----------------------------------

        image_file_id = get_qr(
            qr_number
        )

        if not image_file_id:

            bot.send_message(
                message.chat.id,
                (
                    f"⚠️ QR {qr_number} abhi set nahi hai.\n\n"
                    f"Pehle <code>/setqr {qr_number}</code> "
                    "se QR set karo."
                ),
                parse_mode="HTML"
            )

            return

        # ----------------------------------
        # UPI
        # ----------------------------------

        upi_id = get_qr_upi(
            qr_number
        )

        if upi_id:

            upi_text = (
                "\n\n"
                "💳 <b>UPI ID</b>\n"
                f"<code>{upi_id}</code>"
            )

        else:

            upi_text = (
                "\n\n"
                "💳 <b>UPI ID</b>\n"
                "<code>No UPI added here</code>"
            )

        # ----------------------------------
        # USERS
        # ----------------------------------

        user_1_id = active_deal["user_1_id"]
        user_2_id = active_deal["user_2_id"]

        try:

            user_1 = bot.get_chat(
                user_1_id
            )

            user_2 = bot.get_chat(
                user_2_id
            )

            user_1_name = (
                user_1.first_name
                or "User 1"
            )

            user_2_name = (
                user_2.first_name
                or "User 2"
            )

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
        # AMOUNT TEXT
        # ----------------------------------

        amount_text = f"₹{amount:g}"
        fee_text = f"₹{fee:g}"
        total_text = f"₹{total:g}"

        # ----------------------------------
        # CAPTION
        # ----------------------------------

        caption = (
            f"💳 <b>This is QR {qr_number}</b>\n\n"
            f"Please pay <b>{total_text}</b> on this QR.\n\n"
            f"💰 Amount: {amount_text}\n"
            f"💸 MM Fee: {fee_text}\n"
            f"💳 Total: <b>{total_text}</b>"
            f"{upi_text}\n\n"
            f"👤 {mention_1}\n"
            f"👤 {mention_2}"
        )

        # ----------------------------------
        # SEND QR
        # ----------------------------------

        try:

            bot.send_photo(
                message.chat.id,
                image_file_id,
                caption=caption,
                parse_mode="HTML"
            )

        except Exception as error:

            print(
                f"QR send error: {error}"
            )

            bot.send_message(
                message.chat.id,
                "⚠️ QR send karte time error aa gaya."
            )
