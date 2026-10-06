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
    get_mm_stats,
    get_total_users,
    get_active_users
)

broadcast_waiting = set()


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

        bot.send_message(
            call.message.chat.id,
            (
                "📢 <b>BROADCAST</b>\n\n"
                "Jo message sabhi users ko bhejna hai, "
                "ab woh message send karo.\n\n"
                "⚠️ Text, photo, video ya document bhej sakte ho."
            ),
            parse_mode="HTML"
        )

        broadcast_waiting.add(
            call.from_user.id
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
            "📢 Broadcast start ho gaya...\n\n"
            "⏳ Please wait."
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

                "💸 <code>.payment amount</code>\n"
                "Payment complete karne ke liye.\n\n"

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
            return f"₹{float(value):g}"

        text = (
            "📊 <b>TODAY'S REPORT</b>\n\n"

            f"📅 Date: <b>{stats['date']}</b>\n\n"

            "🤝 <b>DEALS</b>\n"
            f"• Created: <b>{stats['total_deals']}</b>\n"
            f"• Completed: <b>{stats['completed_deals']}</b>\n"
            f"• Pending: <b>{stats['pending_deals']}</b>\n\n"

            "💰 <b>PAYMENT</b>\n"
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
            f"• Total Amount: <b>₹{float(total_amount):g}</b>\n\n"

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

        deals = get_deals_by_date(
            today
        )

        if not deals:

            text = (
                "📋 <b>DEAL HISTORY</b>\n\n"
                f"📅 {today}\n\n"
                "❌ Aaj koi deal nahi mili."
            )

        else:

            lines = [
                "📋 <b>DEAL HISTORY</b>",
                "",
                f"📅 {today}",
                ""
            ]

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
                        f"⚡ Action: <b>{deal['final_action']}</b>"
                    )

                lines.append("")

            text = "\n".join(lines)

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
                    os.remove(backup_file)
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
