from telebot import types

from config import ADMIN_IDS


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
