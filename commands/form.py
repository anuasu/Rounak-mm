from config import MM_CHAT_IDS, ADMIN_IDS

from database.database import get_active_deal


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
# REGISTER FORM
# ==========================================

def register_form(bot):

    @bot.message_handler(
        func=lambda message:
        message.text
        and message.text.strip().lower() == ".form"
    )
    def form_command(message):

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
        # GET ACTIVE DEAL
        # ==================================

        active_deal = get_active_deal(
            message.chat.id
        )

        if not active_deal:

            bot.reply_to(
                message,
                "⚠️ Is group mein koi active deal nahi hai."
            )

            return

        # ==================================
        # GET USERS
        # ==================================

        user_1_id = active_deal["user_1_id"]
        user_2_id = active_deal["user_2_id"]

        try:

            user_1 = bot.get_chat(user_1_id)
            user_2 = bot.get_chat(user_2_id)

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
                f"Form user lookup error: {error}"
            )

            user_1_name = "User 1"
            user_2_name = "User 2"

        # ==================================
        # USER MENTIONS
        # ==================================

        user_1_mention = user_mention(
            user_1_id,
            user_1_name
        )

        user_2_mention = user_mention(
            user_2_id,
            user_2_name
        )

        # ==================================
        # DEAL AMOUNT
        # ==================================

        deal_amount = (
            active_deal["deal_amount"]
            or 0
        )

        amount_text = f"₹{deal_amount:g}"

        # ==================================
        # FORM TEXT
        # ==================================

        form_text = f"""
━━━━━━━━━━━━━━━━━━━
 𝐑𝐎𝐔𝐍𝐀𝐊 𝐌𝐌 𝐃𝐄𝐀𝐋 𝐅𝐎𝐑𝐌
━━━━━━━━━━━━━━━━━━━
 • 𝑺𝒆𝒍𝒍𝒆𝒓 : {user_1_mention}
 • 𝑩𝒖𝒚𝒆𝒓 : {user_2_mention}
 • 𝑻𝒐𝒕𝒂𝒍 𝑫𝒆𝒂𝒍 𝑨𝒎𝒐𝒖𝒏𝒕 : {amount_text}
 • 𝑹𝒆𝒍𝒆𝒂𝒔𝒆 𝑪𝒐𝒏𝒅𝒊𝒕𝒊𝒐𝒏 :
━━━━━━━━━━━━━━━━━━━
      ⚠️ 𝐁𝐞 𝐀𝐥𝐞𝐫𝐭 𝐅𝐫𝐨𝐦 𝐂𝐥𝐨𝐧𝐞
🦅 <b>FORM BY @ROUNAKMM 🐢</b>
━━━━━━━━━━━━━━━━━━━
"""

        # ==================================
        # SEND FORM
        # ==================================

        bot.send_message(
            message.chat.id,
            form_text,
            parse_mode="HTML"
  )
