from telebot import types
from config import ADMIN_IDS, BACKUP_TIMEZONE
import json
import os
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

from database.database import (
    get_backup_data,
    restore_backup_data
)

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

        # ----------------------------------
        # ADMIN ONLY
        # ----------------------------------

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


    # ==========================================
# AUTOMATIC DAILY BACKUP
# ==========================================

def automatic_backup(bot):

    while True:

        try:

            now = datetime.now(
                ZoneInfo(BACKUP_TIMEZONE)
            )

            # 12:00 AM check
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

                # ----------------------------------
                # SEND TO ALL ADMINS
                # ----------------------------------

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

                # ----------------------------------
                # DELETE TEMP FILE
                # ----------------------------------

                try:
                    os.remove(backup_file)
                except Exception:
                    pass

                # Same minute mein dobara na chale
                while True:

                    current_time = datetime.now(
                        ZoneInfo(BACKUP_TIMEZONE)
                    )

                    if current_time.minute != 0:
                        break

                    import time
                    time.sleep(5)

            else:

                import time
                time.sleep(20)

        except Exception as error:

            print(
                f"Automatic backup error: {error}"
            )

            import time
            time.sleep(30)

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
    # RECEIVE RESTORE FILE
    # ======================================

    @bot.message_handler(
        content_types=["document"]
    )
    def restore_document(message):

        # ADMIN ONLY
        if message.from_user.id not in ADMIN_IDS:
            return

        # FILE CHECK
        if not message.document.file_name:
            return

        if not message.document.file_name.lower().endswith(".json"):
            bot.reply_to(
                message,
                "❌ Sirf .json backup file send karo."
            )
            return

        try:

            # GET TELEGRAM FILE
            file_info = bot.get_file(
                message.document.file_id
            )

            downloaded_file = bot.download_file(
                file_info.file_path
            )

            # READ JSON
            backup_data = json.loads(
                downloaded_file.decode("utf-8")
            )

            # ==================================
            # VALIDATE BACKUP
            # ==================================

            if (
                "raunak_mm" not in backup_data
                or "users" not in backup_data
            ):
                bot.reply_to(
                    message,
                    "❌ Invalid Raunak MM backup file."
                )
                return

            # ==================================
            # RESTORE
            # ==================================

            success = restore_backup_data(
                backup_data
            )

            if success:

                raunak = backup_data["raunak_mm"]

                bot.reply_to(
                    message,
                    (
                        "✅ <b>DATA RESTORED</b>\n\n"
                        f"👑 Deals: "
                        f"<b>{raunak.get('total_deals', 0)}</b>\n"
                        f"💰 Amount: "
                        f"<b>₹{raunak.get('total_amount', 0):g}</b>\n"
                        f"👥 Users: "
                        f"<b>{len(backup_data.get('users', []))}</b>\n\n"
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
                "Broadcast system yahan add hoga."
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

                "💸 <code>.payment amount</code>\n"
                "Payment complete karne ke liye.\n\n"

                "⏸️ <code>.hold amount</code>\n"
                "Payment hold karne ke liye.\n\n"

                "🧾 <code>.voucher amount</code>\n"
                "Voucher generate karne ke liye.\n\n"

                "📋 <code>.form</code>\n"
                "Blank deal form ke liye.\n\n"

                "📱 <code>.qr1</code> - <code>.qr10</code>\n"
                "QR payment ke liye.\n\n"

                "🗑️ <code>.removedeal</code>\n"
                "Pending/active deal remove karne ke liye.\n\n"

                "🏆 <b>Leaderboard</b>\n"
                "MM aur users ki deal statistics."
            ),
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
# START AUTOMATIC BACKUP
# ==========================================

def start_automatic_backup(bot):

    backup_thread = threading.Thread(
        target=automatic_backup,
        args=(bot,),
        daemon=True
    )

    backup_thread.start()





