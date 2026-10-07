from telebot import types
from config import ADMIN_IDS, BACKUP_TIMEZONE

import json
import os
import threading
import time

from datetime import datetime
from zoneinfo import ZoneInfo

from database.database import (
    get_backup_data,
    restore_backup_data,
    get_connection,
    get_daily_summary,
    get_deals_by_date,
    get_deal_events,
    get_deal_history_with_users,
    get_deal_events_with_users,
    get_mm_stats,
    get_total_users,
    get_active_users
)


# ==========================================
# WAITING STATES
# ==========================================

broadcast_waiting = set()
history_date_waiting = set()


# ==========================================
# ADMIN PANEL KEYBOARD
# ==========================================

def admin_panel_keyboard():

    keyboard = types.InlineKeyboardMarkup(
        row_width=1
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "💾 Backup / Restore",
            callback_data="admin_backup"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "📢 Broadcast",
            callback_data="admin_broadcast"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "❓ Help",
            callback_data="admin_help"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "📊 Detailed Stats",
            callback_data="admin_stats"
        )
    )

    return keyboard


# ==========================================
# BACKUP KEYBOARD
# ==========================================

def backup_keyboard():

    keyboard = types.InlineKeyboardMarkup(
        row_width=1
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "📤 Manual Backup",
            callback_data="manual_backup"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "📥 Restore Data",
            callback_data="restore_data"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "⬅️ Back",
            callback_data="admin_panel_back"
        )
    )

    return keyboard


# ==========================================
# STATS KEYBOARD
# ==========================================

def stats_keyboard():

    keyboard = types.InlineKeyboardMarkup(
        row_width=1
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "📊 Today's Report",
            callback_data="stats_today"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "📋 Deal History",
            callback_data="stats_history"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "📈 Overall Statistics",
            callback_data="stats_overall"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "⬅️ Back",
            callback_data="admin_panel_back"
        )
    )

    return keyboard


# ==========================================
# DEAL HISTORY KEYBOARD
# ==========================================

def deal_history_keyboard():

    keyboard = types.InlineKeyboardMarkup(
        row_width=1
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "🔎 Search Date",
            callback_data="history_search_date"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "📅 Today",
            callback_data="stats_history_today"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "⬅️ Back",
            callback_data="admin_stats"
        )
    )

    return keyboard


# ==========================================
# SHOW DEAL HISTORY
# ==========================================

def show_deal_history(
    bot,
    chat_id,
    message_id,
    date_text
):

    deals = get_deals_by_date(
        date_text
    )

    # ======================================
    # NO DEALS
    # ======================================

    if not deals:

        text = (
            "📋 <b>DEAL HISTORY</b>\n\n"
            f"📅 Date: <b>{date_text}</b>\n\n"
            "❌ Is date par koi deal nahi mili."
        )

        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            reply_markup=deal_history_keyboard(),
            parse_mode="HTML"
        )

        return


    # ======================================
    # DEAL LIST
    # ======================================

    lines = [
        "📋 <b>DEAL HISTORY</b>",
        "",
        f"📅 Date: <b>{date_text}</b>",
        "",
        f"🤝 Total Deals: <b>{len(deals)}</b>",
        ""
    ]

    keyboard = types.InlineKeyboardMarkup(
        row_width=1
    )

    for deal in deals:

        if deal["status"] == "completed":
            status = "✅ Completed"
        else:
            status = "⏳ Pending"

        lines.append(
            f"🤝 <b>Deal #{deal['deal_id']}</b>"
        )

        lines.append(
            f"💰 Amount: ₹{float(deal['deal_amount'] or 0):g}"
        )

        lines.append(
            f"📌 Status: {status}"
        )

        if deal["final_action"]:

            lines.append(
                f"⚡ Action: <b>{str(deal['final_action']).upper()}</b>"
            )

        lines.append("")

        keyboard.add(
            types.InlineKeyboardButton(
                f"🤝 Deal #{deal['deal_id']}",
                callback_data=f"history_deal_{deal['deal_id']}"
            )
        )

    keyboard.add(
        types.InlineKeyboardButton(
            "🔎 Search Another Date",
            callback_data="history_search_date"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "⬅️ Back",
            callback_data="admin_stats"
        )
    )

    bot.edit_message_text(
        "\n".join(lines),
        chat_id,
        message_id,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# ==========================================
# REGISTER ADMIN PANEL
# ==========================================

def register_admin_panel(bot):

    # ======================================
    # /admin
    # ======================================

    @bot.message_handler(commands=["admin"])
    def admin_command(message):

        if message.from_user.id not in ADMIN_IDS:
            return

        bot.send_message(
            message.chat.id,
            (
                "🛠️ <b>ROUNAK MM ADMIN PANEL</b>\n\n"
                "Neeche se option select karo:"
            ),
            reply_markup=admin_panel_keyboard(),
            parse_mode="HTML"
        )


    # ======================================
    # BACKUP / RESTORE
    # ======================================

    @bot.callback_query_handler(
        func=lambda call:
        call.data == "admin_backup"
    )
    def admin_backup(call):

        if call.from_user.id not in ADMIN_IDS:

            bot.answer_callback_query(
                call.id,
                "❌ Access denied.",
                show_alert=True
            )
            return

        bot.answer_callback_query(call.id)

        bot.edit_message_text(
            (
                "💾 <b>BACKUP / RESTORE</b>\n\n"
                "Yahan se leaderboard data ka "
                "backup ya restore manage kar sakte ho."
            ),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=backup_keyboard(),
            parse_mode="HTML"
        )


    # ======================================
    # MANUAL BACKUP
    # ======================================

    @bot.callback_query_handler(
        func=lambda call:
        call.data == "manual_backup"
    )
    def manual_backup(call):

        if call.from_user.id not in ADMIN_IDS:

            bot.answer_callback_query(
                call.id,
                "❌ Access denied.",
                show_alert=True
            )
            return

        bot.answer_callback_query(
            call.id,
            "📤 Backup preparing..."
        )

        try:

            backup_data = get_backup_data()

            backup_text = json.dumps(
                backup_data,
                indent=4,
                ensure_ascii=False
            )

            backup_file = "raunak_mm_backup.json"

            with open(
                backup_file,
                "w",
                encoding="utf-8"
            ) as file:

                file.write(backup_text)

            with open(
                backup_file,
                "rb"
            ) as file:

                bot.send_document(
                    call.message.chat.id,
                    file,
                    caption=(
                        "💾 <b>RAUNAK MM BACKUP</b>\n\n"
                        "✅ Leaderboard data successfully extracted."
                    ),
                    parse_mode="HTML"
                )

        except Exception as error:

            print(
                f"Manual backup error: {error}"
            )

            bot.send_message(
                call.message.chat.id,
                "❌ Backup create karte waqt error aa gaya."
            )


    # ======================================
    # RESTORE DATA BUTTON
    # ======================================

    @bot.callback_query_handler(
        func=lambda call:
        call.data == "restore_data"
    )
    def restore_data_button(call):

        if call.from_user.id not in ADMIN_IDS:

            bot.answer_callback_query(
                call.id,
                "❌ Access denied.",
                show_alert=True
            )
            return

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            (
                "📥 <b>RESTORE DATA</b>\n\n"
                "Apna <code>raunak_mm_backup.json</code> "
                "file yahan send karo.\n\n"
                "⚠️ Sirf Raunak MM ka valid backup "
                "file send karo."
            ),
            parse_mode="HTML"
        )


    # ======================================
    # RECEIVE RESTORE FILE
    # ======================================

    @bot.message_handler(
        content_types=["document"]
    )
    def restore_document(message):

        if message.from_user.id not in ADMIN_IDS:
            return

        if not message.document.file_name:
            return

        if not message.document.file_name.lower().endswith(".json"):

            bot.reply_to(
                message,
                "❌ Sirf .json backup file send karo."
            )
            return

        try:

            file_info = bot.get_file(
                message.document.file_id
            )

            downloaded_file = bot.download_file(
                file_info.file_path
            )

            backup_data = json.loads(
                downloaded_file.decode("utf-8")
            )

            success = restore_backup_data(
                backup_data
            )

            if success:

                bot.reply_to(
                    message,
                    (
                        "✅ <b>DATA RESTORED</b>\n\n"
                        "🏆 Leaderboard data successfully restored."
                    ),
                    parse_mode="HTML"
                )

            else:

                bot.reply_to(
                    message,
                    "❌ Data restore failed."
                )

        except json.JSONDecodeError:

            bot.reply_to(
                message,
                "❌ Backup file valid JSON nahi hai."
            )

        except Exception as error:

            print(
                f"Restore document error: {error}"
            )

            bot.reply_to(
                message,
                "❌ Restore karte waqt error aa gaya."
            )


    # ======================================
    # BROADCAST
    # ======================================

    @bot.callback_query_handler(
        func=lambda call:
        call.data == "admin_broadcast"
    )
    def admin_broadcast(call):

        if call.from_user.id not in ADMIN_IDS:

            bot.answer_callback_query(
                call.id,
                "❌ Access denied.",
                show_alert=True
            )
            return

        bot.answer_callback_query(call.id)

        broadcast_waiting.add(
            call.from_user.id
        )

        keyboard = types.InlineKeyboardMarkup()

        keyboard.add(
            types.InlineKeyboardButton(
                "❌ Cancel Broadcast",
                callback_data="cancel_broadcast"
            )
        )

        bot.send_message(
            call.message.chat.id,
            (
                "📢 <b>BROADCAST</b>\n\n"
                "Jo message sabhi users ko bhejna hai, "
                "ab woh message send karo.\n\n"
                "⚠️ Text, photo, video ya document bhej sakte ho."
            ),
            reply_markup=keyboard,
            parse_mode="HTML"
        )


    # ======================================
    # CANCEL BROADCAST
    # ======================================

    @bot.callback_query_handler(
        func=lambda call:
        call.data == "cancel_broadcast"
    )
    def cancel_broadcast(call):

        if call.from_user.id not in ADMIN_IDS:

            bot.answer_callback_query(
                call.id,
                "❌ Access denied.",
                show_alert=True
            )
            return

        broadcast_waiting.discard(
            call.from_user.id
        )

        bot.answer_callback_query(
            call.id,
            "Broadcast cancelled."
        )

        bot.edit_message_text(
            (
                "❌ <b>BROADCAST CANCELLED</b>\n\n"
                "Broadcast nahi bheja gaya."
            ),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=admin_panel_keyboard(),
            parse_mode="HTML"
        )


    # ======================================
    # RECEIVE BROADCAST MESSAGE
    # ======================================

    @bot.message_handler(
        func=lambda message:
        message.from_user.id in broadcast_waiting,
        content_types=[
            "text",
            "photo",
            "video",
            "document",
            "audio",
            "voice",
            "animation"
        ]
    )
    def receive_broadcast(message):

        if message.from_user.id not in ADMIN_IDS:
            return

        broadcast_waiting.discard(
            message.from_user.id
        )

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT chat_id
            FROM users
        """)

        users = cursor.fetchall()

        connection.close()

        sent = 0
        failed = 0

        bot.reply_to(
            message,
            (
                "📢 Broadcast start ho gaya...\n\n"
                "⏳ Please wait."
            )
        )

        for user in users:

            user_id = user["chat_id"]

            try:

                bot.copy_message(
                    user_id,
                    message.chat.id,
                    message.message_id
                )

                sent += 1

            except Exception as error:

                failed += 1

                print(
                    f"Broadcast failed for {user_id}: {error}"
                )

            time.sleep(0.05)

        bot.send_message(
            message.chat.id,
            (
                "📢 <b>BROADCAST COMPLETED</b>\n\n"
                f"👥 Total Users: <b>{len(users)}</b>\n"
                f"✅ Sent: <b>{sent}</b>\n"
                f"❌ Failed: <b>{failed}</b>"
            ),
            parse_mode="HTML"
        )


    # ======================================
    # HELP
    # ======================================

    @bot.callback_query_handler(
        func=lambda call:
        call.data == "admin_help"
    )
    def admin_help(call):

        if call.from_user.id not in ADMIN_IDS:

            bot.answer_callback_query(
                call.id,
                "❌ Access denied.",
                show_alert=True
            )
            return

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            (
                "❓ <b>ROUNAK MM HELP</b>\n\n"

                "🤝 <code>.deal</code>\n"
                "New deal start karne ke liye.\n\n"

                "🗑️ <code>.removedeal</code>\n"
                "Pending/active deal remove karne ke liye.\n\n"

                "📋 <code>.form</code>\n"
                "Blank deal form ke liye.\n\n"

                "⏸️ <code>.hold amount</code>\n"
                "Payment hold karne ke liye.\n\n"

                "📱 <code>.qr1</code> - <code>.qr10</code>\n"
                "QR payment ke liye.\n\n"

                                "💸 <code>.release amount</code>\n"
                "Payment release karne ke liye.\n\n"

                "↩️ <code>.refund amount</code>\n"
                "Payment refund karne ke liye.\n\n"

                "⚖️ <code>.split</code>\n"
                "Payment ko release/refund mein split karne ke liye.\n\n"

                "🧾 <code>.voucher amount</code>\n"
                "Voucher generate karne ke liye.\n\n"

                "⚙️ <code>/setfee</code>\n"
                "MM fee image set/update karne ke liye.\n\n"

                "📱 <code>/setqr 1</code> - <code>/setqr 10</code>\n"
                "QR payment image set/update karne ke liye.\n\n"

                "🧹 <code>/clean</code>\n"
                "GC members aur tracked messages clean "
                "karke new invite link generate karne ke liye.\n\n"

                "🏆 <b>Leaderboard</b>\n"
                "MM aur users ki deal statistics."
            ),
            parse_mode="HTML"
        )


    # ======================================
    # DETAILED STATS
    # ======================================

    @bot.callback_query_handler(
        func=lambda call:
        call.data == "admin_stats"
    )
    def admin_stats(call):

        if call.from_user.id not in ADMIN_IDS:

            bot.answer_callback_query(
                call.id,
                "❌ Access denied.",
                show_alert=True
            )
            return

        bot.answer_callback_query(call.id)

        bot.edit_message_text(
            (
                "📊 <b>DETAILED STATISTICS</b>\n\n"
                "Yahan se Rounak MM ki complete "
                "payment aur deal activity check karo."
            ),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=stats_keyboard(),
            parse_mode="HTML"
        )


    # ======================================
    # TODAY'S REPORT
    # ======================================

    @bot.callback_query_handler(
        func=lambda call:
        call.data == "stats_today"
    )
    def stats_today(call):

        if call.from_user.id not in ADMIN_IDS:

            bot.answer_callback_query(
                call.id,
                "❌ Access denied.",
                show_alert=True
            )
            return

        bot.answer_callback_query(call.id)

        today = datetime.now().strftime(
            "%Y-%m-%d"
        )

        stats = get_daily_summary(
            today
        )

        def money(value):
            return f"₹{float(value or 0):g}"

        text = (
            "📊 <b>TODAY'S REPORT</b>\n\n"

            f"📅 Date: <b>{stats['date']}</b>\n\n"

            "🤝 <b>DEALS</b>\n"
            f"• Created: <b>{stats['total_deals']}</b>\n"
            f"• Completed: <b>{stats['completed_deals']}</b>\n"
            f"• Pending: <b>{stats['pending_deals']}</b>\n\n"

            "💰 <b>AMOUNTS</b>\n"
            f"• Deal Amount: <b>{money(stats['total_amount'])}</b>\n"
            f"• Payment: <b>{money(stats['total_payment'])}</b>\n"
            f"• Hold: <b>{money(stats['total_hold'])}</b>\n\n"

            "💎 <b>MM</b>\n"
            f"• MM Fee: <b>{money(stats['total_fee'])}</b>\n\n"

            "💸 <b>FINAL TRANSACTIONS</b>\n"
            f"• Release: <b>{money(stats['total_release'])}</b>\n"
            f"• Refund: <b>{money(stats['total_refund'])}</b>"
        )

        keyboard = types.InlineKeyboardMarkup()

        keyboard.add(
            types.InlineKeyboardButton(
                "⬅️ Back",
                callback_data="admin_stats"
            )
        )

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard,
            parse_mode="HTML"
        )


    # ======================================
    # OVERALL STATISTICS
    # ======================================

    @bot.callback_query_handler(
        func=lambda call:
        call.data == "stats_overall"
    )
    def stats_overall(call):

        if call.from_user.id not in ADMIN_IDS:

            bot.answer_callback_query(
                call.id,
                "❌ Access denied.",
                show_alert=True
            )
            return

        bot.answer_callback_query(call.id)

        mm_stats = get_mm_stats()

        total_users = get_total_users()
        active_users = get_active_users()

        total_deals = (
            mm_stats["total_deals"]
            if mm_stats
            else 0
        )

        total_amount = (
            mm_stats["total_amount"]
            if mm_stats
            else 0
        )

        text = (
            "📈 <b>OVERALL STATISTICS</b>\n\n"

            "🤝 <b>MM DEALS</b>\n"
            f"• Total Deals: <b>{total_deals}</b>\n"
            f"• Total Amount: <b>₹{float(total_amount or 0):g}</b>\n\n"

            "👥 <b>USERS</b>\n"
            f"• Total Users: <b>{total_users}</b>\n"
            f"• Active Users: <b>{active_users}</b>"
        )

        keyboard = types.InlineKeyboardMarkup()

        keyboard.add(
            types.InlineKeyboardButton(
                "⬅️ Back",
                callback_data="admin_stats"
            )
        )

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard,
            parse_mode="HTML"
        )


    # ======================================
    # DEAL HISTORY
    # ======================================

    @bot.callback_query_handler(
        func=lambda call:
        call.data == "stats_history"
    )
    def stats_history(call):

        if call.from_user.id not in ADMIN_IDS:

            bot.answer_callback_query(
                call.id,
                "❌ Access denied.",
                show_alert=True
            )
            return

        bot.answer_callback_query(call.id)

        today = datetime.now().strftime(
            "%Y-%m-%d"
        )

        show_deal_history(
            bot,
            call.message.chat.id,
            call.message.message_id,
            today
        )


    # ======================================
    # TODAY HISTORY
    # ======================================

    @bot.callback_query_handler(
        func=lambda call:
        call.data == "stats_history_today"
    )
    def stats_history_today(call):

        if call.from_user.id not in ADMIN_IDS:

            bot.answer_callback_query(
                call.id,
                "❌ Access denied.",
                show_alert=True
            )
            return

        bot.answer_callback_query(call.id)

        today = datetime.now().strftime(
            "%Y-%m-%d"
        )

        show_deal_history(
            bot,
            call.message.chat.id,
            call.message.message_id,
            today
        )


    # ======================================
    # SEARCH DEAL HISTORY BY DATE
    # ======================================

    @bot.callback_query_handler(
        func=lambda call:
        call.data == "history_search_date"
    )
    def history_search_date(call):

        if call.from_user.id not in ADMIN_IDS:

            bot.answer_callback_query(
                call.id,
                "❌ Access denied.",
                show_alert=True
            )
            return

        bot.answer_callback_query(call.id)

        history_date_waiting.add(
            call.from_user.id
        )

        keyboard = types.InlineKeyboardMarkup()

        keyboard.add(
            types.InlineKeyboardButton(
                "❌ Cancel",
                callback_data="cancel_history_search"
            )
        )

        bot.send_message(
            call.message.chat.id,
            (
                "🔎 <b>SEARCH DEAL HISTORY</b>\n\n"
                "Jis date ki deals check karni hain "
                "woh date send karo.\n\n"

                "Example:\n"
                "<code>18-10-2026</code>\n"
                "<code>18/10/2026</code>\n"
                "<code>2026-10-18</code>"
            ),
            reply_markup=keyboard,
            parse_mode="HTML"
        )


    # ======================================
    # CANCEL DATE SEARCH
    # ======================================

    @bot.callback_query_handler(
        func=lambda call:
        call.data == "cancel_history_search"
    )
    def cancel_history_search(call):

        if call.from_user.id not in ADMIN_IDS:

            bot.answer_callback_query(
                call.id,
                "❌ Access denied.",
                show_alert=True
            )
            return

        history_date_waiting.discard(
            call.from_user.id
        )

        bot.answer_callback_query(
            call.id,
            "Search cancelled."
        )

        bot.edit_message_text(
            (
                "❌ <b>SEARCH CANCELLED</b>\n\n"
                "Deal history search cancel kar diya gaya."
            ),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=stats_keyboard(),
            parse_mode="HTML"
        )


    # ======================================
    # RECEIVE HISTORY DATE
    # ======================================

    @bot.message_handler(
        func=lambda message:
        message.from_user.id in history_date_waiting,
        content_types=["text"]
    )
    def receive_history_date(message):

        if message.from_user.id not in ADMIN_IDS:
            return

        history_date_waiting.discard(
            message.from_user.id
        )

        date_input = message.text.strip()

        parsed_date = None

        date_formats = [
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%Y-%m-%d"
        ]

        for date_format in date_formats:

            try:

                parsed_date = datetime.strptime(
                    date_input,
                    date_format
                )

                break

            except ValueError:
                continue

        if parsed_date is None:

            keyboard = types.InlineKeyboardMarkup()

            keyboard.add(
                types.InlineKeyboardButton(
                    "🔎 Try Again",
                    callback_data="history_search_date"
                )
            )

            keyboard.add(
                types.InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="admin_stats"
                )
            )

            bot.reply_to(
                message,
                (
                    "❌ <b>INVALID DATE</b>\n\n"
                    "Date is format mein send karo:\n"
                    "<code>18-10-2026</code>\n"
                    "<code>18/10/2026</code>\n"
                    "<code>2026-10-18</code>"
                ),
                reply_markup=keyboard,
                parse_mode="HTML"
            )

            return

        date_text = parsed_date.strftime(
            "%Y-%m-%d"
        )

        # Send history in a new message
        deals = get_deals_by_date(
            date_text
        )

        if not deals:

            keyboard = types.InlineKeyboardMarkup()

            keyboard.add(
                types.InlineKeyboardButton(
                    "🔎 Search Another Date",
                    callback_data="history_search_date"
                )
            )

            keyboard.add(
                types.InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="admin_stats"
                )
            )

            bot.send_message(
                message.chat.id,
                (
                    "📋 <b>DEAL HISTORY</b>\n\n"
                    f"📅 Date: <b>{date_text}</b>\n\n"
                    "❌ Is date par koi deal nahi mili."
                ),
                reply_markup=keyboard,
                parse_mode="HTML"
            )

            return

        lines = [
            "📋 <b>DEAL HISTORY</b>",
            "",
            f"📅 Date: <b>{date_text}</b>",
            "",
            f"🤝 Total Deals: <b>{len(deals)}</b>",
            ""
        ]

        keyboard = types.InlineKeyboardMarkup(
            row_width=1
        )

        for deal in deals:

            status = (
                "✅ Completed"
                if deal["status"] == "completed"
                else "⏳ Pending"
            )

            lines.append(
                f"🤝 <b>Deal #{deal['deal_id']}</b>"
            )

            lines.append(
                f"💰 Amount: ₹{float(deal['deal_amount'] or 0):g}"
            )

            lines.append(
                f"📌 Status: {status}"
            )

            if deal["final_action"]:

                lines.append(
                    f"⚡ Action: <b>{str(deal['final_action']).upper()}</b>"
                )

            lines.append("")

            keyboard.add(
                types.InlineKeyboardButton(
                    f"🤝 Deal #{deal['deal_id']}",
                    callback_data=f"history_deal_{deal['deal_id']}"
                )
            )

        keyboard.add(
            types.InlineKeyboardButton(
                "🔎 Search Another Date",
                callback_data="history_search_date"
            )
        )

        keyboard.add(
            types.InlineKeyboardButton(
                "⬅️ Back",
                callback_data="admin_stats"
            )
        )

        bot.send_message(
            message.chat.id,
            "\n".join(lines),
            reply_markup=keyboard,
            parse_mode="HTML"
        )


    # ======================================
    # FULL DEAL DETAILS
    # ======================================

    @bot.callback_query_handler(
        func=lambda call:
        call.data.startswith("history_deal_")
    )
    def history_deal_details(call):

        if call.from_user.id not in ADMIN_IDS:

            bot.answer_callback_query(
                call.id,
                "❌ Access denied.",
                show_alert=True
            )
            return

        bot.answer_callback_query(call.id)

        try:

            deal_id = int(
                call.data.replace(
                    "history_deal_",
                    ""
                )
            )

        except ValueError:

            bot.answer_callback_query(
                call.id,
                "Invalid deal.",
                show_alert=True
            )
            return

        deal = get_deal_history_with_users(
            deal_id
        )

        if not deal:

            bot.answer_callback_query(
                call.id,
                "Deal not found.",
                show_alert=True
            )
            return

        events = get_deal_events_with_users(
            deal_id
        )

        def money(value):

            return f"₹{float(value or 0):g}"


        def user_name(
            user_id,
            first_name,
            username
        ):

            if username:
                return f"@{username}"

            if first_name:
                return first_name

            if user_id:
                return str(user_id)

            return "Unknown"


        user1 = user_name(
            deal["user_1_id"],
            deal["user_1_name"],
            deal["user_1_username"]
        )

        user2 = user_name(
            deal["user_2_id"],
            deal["user_2_name"],
            deal["user_2_username"]
        )


        status = (
            "✅ Completed"
            if deal["status"] == "completed"
            else "⏳ Pending"
        )


        lines = [
            "📋 <b>DEAL DETAILS</b>",
            "",
            f"🤝 Deal ID: <b>#{deal['deal_id']}</b>",
            f"📌 Status: <b>{status}</b>",
            "",
            "👥 <b>USERS</b>",
            f"• User 1: <b>{user1}</b>",
            f"• User 2: <b>{user2}</b>",
            "",
            "💰 <b>AMOUNTS</b>",
            f"• Deal Amount: <b>{money(deal['deal_amount'])}</b>",
            f"• MM Fee: <b>{money(deal['mm_fee'])}</b>",
            f"• Total Received: <b>{money(deal['total_received'])}</b>",
            f"• Holding: <b>{money(deal['holding_amount'])}</b>",
            "",
            "🕒 <b>TIME</b>",
            f"• Created: <code>{deal['created_at'] or '-'}</code>",
            f"• Hold: <code>{deal['hold_at'] or '-'}</code>",
            f"• Release: <code>{deal['release_at'] or '-'}</code>",
            f"• Refund: <code>{deal['refund_at'] or '-'}</code>",
            f"• Completed: <code>{deal['completed_at'] or '-'}</code>",
            ""
        ]


        # ==================================
        # FINAL ACTION
        # ==================================

        if deal["final_action"]:

            lines.extend([
                "⚡ <b>FINAL ACTION</b>",
                f"• {str(deal['final_action']).upper()}",
                ""
            ])


        # ==================================
        # TRANSACTION EVENTS
        # ==================================

        if events:

            lines.extend([
                "📜 <b>TRANSACTION HISTORY</b>",
                ""
            ])

            for event in events:

                event_type = event["event_type"]

                event_user = user_name(
                    event["user_id"],
                    event["first_name"],
                    event["username"]
                )

                amount = money(
                    event["amount"]
                )


                if event_type == "created":

                    icon = "🆕"
                    title = "Deal Created"

                elif event_type == "payment":

                    icon = "💳"
                    title = "Payment"

                elif event_type == "hold":

                    icon = "⏸️"
                    title = "Payment Hold"

                elif event_type == "release":

                    icon = "💸"
                    title = "Release"

                elif event_type == "refund":

                    icon = "↩️"
                    title = "Refund"

                elif event_type == "split_release":

                    icon = "💸"
                    title = "Split Release"

                elif event_type == "split_refund":

                    icon = "↩️"
                    title = "Split Refund"

                else:

                    icon = "📌"
                    title = event_type


                lines.append(
                    f"{icon} <b>{title}</b>"
                )


                if event["user_id"]:

                    lines.append(
                        f"• User: <b>{event_user}</b>"
                    )


                lines.append(
                    f"• Amount: <b>{amount}</b>"
                )


                if event["mm_fee"]:

                    lines.append(
                        f"• MM Fee: <b>{money(event['mm_fee'])}</b>"
                    )


                lines.append(
                    f"• Time: <code>{event['event_time']}</code>"
                )

                lines.append("")


        keyboard = types.InlineKeyboardMarkup()

        keyboard.add(
            types.InlineKeyboardButton(
                "⬅️ Back to Deal History",
                callback_data="stats_history"
            )
        )

        bot.edit_message_text(
            "\n".join(lines),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard,
            parse_mode="HTML"
        )


    # ======================================
    # BACK TO ADMIN PANEL
    # ======================================

    @bot.callback_query_handler(
        func=lambda call:
        call.data == "admin_panel_back"
    )
    def admin_panel_back(call):

        if call.from_user.id not in ADMIN_IDS:

            bot.answer_callback_query(
                call.id,
                "❌ Access denied.",
                show_alert=True
            )
            return

        bot.answer_callback_query(call.id)

        bot.edit_message_text(
            (
                "🛠️ <b>ROUNAK MM ADMIN PANEL</b>\n\n"
                "Neeche se option select karo:"
            ),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=admin_panel_keyboard(),
            parse_mode="HTML"
        )


# ==========================================
# AUTOMATIC DAILY BACKUP
# ==========================================

def automatic_backup(bot):

    while True:

        try:

            now = datetime.now(
                ZoneInfo(BACKUP_TIMEZONE)
            )

            if now.hour == 0 and now.minute == 0:

                backup_data = get_backup_data()

                backup_text = json.dumps(
                    backup_data,
                    indent=4,
                    ensure_ascii=False
                )

                backup_file = "raunak_mm_auto_backup.json"

                with open(
                    backup_file,
                    "w",
                    encoding="utf-8"
                ) as file:

                    file.write(backup_text)

                for admin_id in ADMIN_IDS:

                    try:

                        with open(
                            backup_file,
                            "rb"
                        ) as file:

                            bot.send_document(
                                admin_id,
                                file,
                                caption=(
                                    "🤖 <b>AUTOMATIC BACKUP</b>\n\n"
                                    "🕛 Daily 12:00 AM backup\n"
                                    "✅ Leaderboard data saved."
                                ),
                                parse_mode="HTML"
                            )

                    except Exception as error:

                        print(
                            f"Automatic backup send error "
                            f"for {admin_id}: {error}"
                        )

                try:

                    os.remove(
                        backup_file
                    )

                except Exception:

                    pass

                time.sleep(60)

            else:

                time.sleep(20)

        except Exception as error:

            print(
                f"Automatic backup error: {error}"
            )

            time.sleep(30)


# ==========================================
# START AUTOMATIC BACKUP
# ==========================================

def start_automatic_backup(bot):

    backup_thread = threading.Thread(
        target=automatic_backup,
        args=(bot,),
        daemon=True
    )

    backup_thread.start()
