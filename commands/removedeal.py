from config import MM_CHAT_IDS, ADMIN_IDS
from database.database import remove_deal


# ==========================================
# REGISTER REMOVE DEAL
# ==========================================

def register_removedeal(bot):

    # ======================================
    # .removedeal
    # ======================================

    @bot.message_handler(
        func=lambda message:
        message.text
        and message.text.strip().lower() == ".removedeal"
    )
    def removedeal_command(message):

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
        # REMOVE ACTIVE DEAL
        # ----------------------------------

        deal_id = remove_deal(
            message.chat.id
        )

        if not deal_id:

            bot.reply_to(
                message,
                "ℹ️ Is group mein koi active deal nahi hai."
            )

            return

        # ----------------------------------
        # SUCCESS
        # ----------------------------------

        bot.reply_to(
            message,
            (
                "🗑️ <b>DEAL REMOVED</b>\n\n"
                f"🤝 Deal ID: <code>#{deal_id}</code>\n"
                "⏳ Status: Cancelled\n\n"
                "Ab fresh <code>.deal</code> se new deal bana sakte ho."
            ),
            parse_mode="HTML"
        )
