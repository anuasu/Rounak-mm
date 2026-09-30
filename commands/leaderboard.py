from database.database import (
    get_leaderboard,
    get_total_user_deals
)


# ==========================================
# LEADERBOARD TEXT
# ==========================================

def build_leaderboard():

    users = get_leaderboard(limit=20)
    total_deals = get_total_user_deals()

    text = "🏆 <b>RAUNAK MM LEADERBOARD</b>\n\n"

    text += f"🤝 Total User Deals: <b>{total_deals}</b>\n"

    text += "\n━━━━━━━━━━━━━━━━━━\n\n"

    if not users:
        text += "📭 Abhi leaderboard mein koi data nahi hai."

        return text

    for position, user in enumerate(users, start=1):

        name = user["first_name"] or "Unknown"

        username = (
            f"@{user['username']}"
            if user["username"]
            else "No Username"
        )

        chat_id = user["chat_id"]
        deals = user["completed_deals"]
        amount = user["total_deal_amount"]

        text += (
            f"<b>#{position} {name}</b>\n"
            f"👤 {username}\n"
            f"🆔 <code>{chat_id}</code>\n"
            f"🤝 Deals: <b>{deals}</b>\n"
            f"💰 Amount: <b>₹{amount:g}</b>\n\n"
        )

    return text


# ==========================================
# REGISTER LEADERBOARD
# ==========================================

def register_leaderboard(bot):

    @bot.callback_query_handler(
        func=lambda call: call.data == "leaderboard"
    )
    def leaderboard_callback(call):

        bot.answer_callback_query(call.id)

        text = build_leaderboard()

        bot.send_message(
            call.message.chat.id,
            text,
            parse_mode="HTML"
        )
