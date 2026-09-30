from config import MM_CHAT_IDS, ADMIN_IDS

from database.database import (
    get_mm_fee_image,
    set_mm_fee_image
)


# ==========================================
# REGISTER MM FEE
# ==========================================

def register_mm_fee(bot):

    # ======================================
    # 💰 WHAT MM FEE? BUTTON
    # ======================================

    @bot.callback_query_handler(
        func=lambda call: call.data == "mm_fee"
    )
    def mm_fee_callback(call):

        # ----------------------------------
        # GET SAVED IMAGE
        # ----------------------------------

        image_file_id = get_mm_fee_image()

        # ----------------------------------
        # IMAGE NOT SET
        # ----------------------------------

        if not image_file_id:

            bot.answer_callback_query(
                call.id,
                "⚠️ MM Fee image abhi set nahi hai.",
                show_alert=True
            )

            return

        # ----------------------------------
        # ANSWER CALLBACK
        # ----------------------------------

        bot.answer_callback_query(
            call.id
        )

        # ----------------------------------
        # SEND IMAGE
        # ----------------------------------

        bot.send_photo(
            call.message.chat.id,
            image_file_id,
            caption="💰 <b>RAUNAK MM FEES</b>",
            parse_mode="HTML"
        )


    # ======================================
    # /setfee
    # ======================================

    @bot.message_handler(
        commands=["setfee"]
    )
    def set_fee_command(message):

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
        # CHECK REPLY
        # ----------------------------------

        if not message.reply_to_message:

            bot.reply_to(
                message,
                (
                    "⚠️ Fees image ko reply karke "
                    "<code>/setfee</code> bhejo."
                ),
                parse_mode="HTML"
            )

            return

        # ----------------------------------
        # CHECK PHOTO
        # ----------------------------------

        replied_message = message.reply_to_message

        if not replied_message.photo:

            bot.reply_to(
                message,
                "⚠️ Reply kiya hua message ek photo hona chahiye."
            )

            return

        # ----------------------------------
        # GET FILE ID
        # ----------------------------------

        image_file_id = (
            replied_message.photo[-1].file_id
        )

        # ----------------------------------
        # SAVE IMAGE
        # ----------------------------------

        set_mm_fee_image(
            image_file_id
        )

        # ----------------------------------
        # SUCCESS
        # ----------------------------------

        bot.reply_to(
            message,
            (
                "✅ <b>MM Fee Image Updated!</b>\n\n"
                "Ab users <b>💰 What MM Fee?</b> "
                "button se ye image dekh sakte hain."
            ),
            parse_mode="HTML"
        )
