from telebot import types

from database.database import (
    get_leaderboard,
    get_total_user_deals,
    get_total_users,
    get_active_users,
    get_connection
)


# ==========================================
# GET RAUNAK MM TOTAL STATS
# ==========================================

def get_leaderboard_mm_stats():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            total_deals,
            total_amount
        FROM leaderboard_stats
        WHERE id = 1
    """)

    stats = cursor.fetchone()

    connection.close()

    if not stats:
        return {
            "total_deals": 0,
            "total_amount": 0
        }

    return {
        "total_deals": stats["total_deals"] or 0,
        "total_amount": stats["total_amount"] or 0
    }


# ==========================================
# BUILD LEADERBOARD
# ==========================================

def build_leaderboard():

    users = get_leaderboard(limit=20)

    total_user_deals = get_total_user_deals()

    mm_stats = get_leaderboard_mm_stats()

    total_users = get_total_users()
    active_users = get_active_users()

    mm_total_deals = mm_stats["total_deals"]
    mm_total_amount = mm_stats["total_amount"]

    # ======================================
    # HEADER
    # ======================================

    text = (
        "🏆 <b>ROUNAK MM LEADERBOARD</b>\n\n"

        "👑 <b>ROUNAK MM</b>\n"
        f"🤝 Total Deals: <b>{mm_total_deals}</b>\n"
        f"💰 Total Deal Amount: <b>₹{mm_total_amount:g}</b>\n\n"

        "━━━━━━━━━━━━━━━━━━\n\n"

        "👥 <b>COMMUNITY STATS</b>\n"
        f"👤 Total Users: <b>{total_users}</b>\n"
        f"🟢 Active Users: <b>{active_users}</b>\n\n"

        "━━━━━━━━━━━━━━━━━━\n\n"

        f"🤝 Total User Deals: <b>{total_user_deals}</b>\n\n"
    )

    # ======================================
    # EMPTY LEADERBOARD
    # ======================================

    if not users:

        text += (
            "🏆 <b>Leaderboard is Empty</b>\n"
            "No user data is available yet."
        )

        return text

    # ======================================
    # USERS
    # ======================================

    text += "👥 <b>USERS</b>\n\n"

    for position, user in enumerate(users, start=1):

        name = user["first_name"] or "Unknown"

        username = (
            f"@{user['username']}"
            if user["username"]
            else "No Username"
        )

        chat_id = user["chat_id"]

        deals = user["completed_deals"] or 0

        amount = user["total_deal_amount"] or 0

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

        keyboard = types.InlineKeyboardMarkup()

        keyboard.add(
            types.InlineKeyboardButton(
                "🔎 Search User ID",
                callback_data="search_user"
            )
        )

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
