@bot.message_handler(
    func=lambda message:
    message.text
    and message.text.strip().lower() == ".removedeal"
)
def remove_deal_command(message):

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

    group_id = message.chat.id

    # ==================================
    # REMOVE PENDING SETUP
    # ==================================

    if group_id in pending_deal_users:

        pending_deal_users.pop(
            group_id,
            None
        )

        bot.reply_to(
            message,
            (
                "🗑️ <b>DEAL REMOVED</b>\n\n"
                "Pending deal setup clear ho gaya.\n\n"
                "Ab fresh <code>.deal</code> se start kar sakte ho."
            ),
            parse_mode="HTML"
        )

        return

    # ==================================
    # REMOVE ACTIVE DATABASE DEAL
    # ==================================

    deal_id = remove_deal(group_id)

    if deal_id:

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

        return

    # ==================================
    # NOTHING TO REMOVE
    # ==================================

    bot.reply_to(
        message,
        "ℹ️ Is group mein koi active deal nahi hai."
    )
