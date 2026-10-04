from config import MM_CHAT_IDS, ADMIN_IDS

from commands.command_utils import (
    normalize_command,
    delete_command_message
)


# ==========================================
# REGISTER FORM
# ==========================================

def register_form(bot):

    @bot.message_handler(
        func=lambda message:
        message.text
        and normalize_command(message.text)
        .lower()
        == ".form"
    )
    def form_command(message):

        # ==================================
        # NORMALIZE COMMAND
        # ==================================

        command_text = normalize_command(
            message.text
        )

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
        # BLANK FORM
        # ==================================

        form_text = f"""
━━━━━━━━━━━━━━━━━━━
 𝐑𝐎𝐔𝐍𝐀𝐊 𝐌𝐌 𝐃𝐄𝐀𝐋 𝐅𝐎𝐑𝐌
━━━━━━━━━━━━━━━━━━━
 • 𝑺𝒆𝒍𝒍𝒆𝒓 :
 • 𝑩𝒖𝒚𝒆𝒓 :
 • 𝑻𝒐𝒕𝒂𝒍 𝑫𝒆𝒂𝒍 𝑨𝒎𝒐𝒖𝒏𝒕 :
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

        # ==================================
        # DELETE COMMAND MESSAGE
        # ==================================

        delete_command_message(
            bot,
            message
        )
