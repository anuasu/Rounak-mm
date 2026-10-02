from config import ADMIN_IDS


# =========================================================
# TEMPORARY MEMORY
# =========================================================

tracked_messages = {}
tracked_users = {}

# Bot ne jo invite link generate kiya hai
managed_invite_links = {}

# Bot ne jo invite-link message bheja tha uska message ID
managed_link_messages = {}


# =========================================================
# TRACK MESSAGE
# =========================================================

def track_message(message):

    if not message:
        return

    chat = getattr(message, "chat", None)

    if not chat:
        return

    if chat.type not in ["group", "supergroup"]:
        return

    chat_id = chat.id

    tracked_messages.setdefault(
        chat_id,
        set()
    ).add(message.message_id)

    user = getattr(
        message,
        "from_user",
        None
    )

    if user:
        tracked_users.setdefault(
            chat_id,
            set()
        ).add(user.id)


# =========================================================
# INSTALL MESSAGE TRACKER
# =========================================================

def install_message_tracker(bot):

    print("🧠 CLEAN MEMORY TRACKER INSTALLING...")

    original_process = bot.process_new_messages

    def tracked_process(messages):

        for message in messages:

            try:
                track_message(message)

            except Exception as error:
                print(
                    f"⚠️ Message tracking error: {error}"
                )

        return original_process(messages)

    bot.process_new_messages = tracked_process


    # =====================================================
    # TRACK BOT SENT MESSAGES
    # =====================================================

    methods = [
        "send_message",
        "send_photo",
        "send_video",
        "send_document",
        "send_audio",
        "send_voice",
        "send_animation",
        "send_sticker",
        "send_video_note",
        "send_location",
        "send_contact",
        "send_venue",
        "send_poll",
        "send_dice",
        "send_invoice",
        "send_game",
        "send_media_group"
    ]

    for method_name in methods:

        original_method = getattr(
            bot,
            method_name,
            None
        )

        if not original_method:
            continue

        def make_wrapper(original, name):

            def wrapper(*args, **kwargs):

                result = original(
                    *args,
                    **kwargs
                )

                try:

                    if isinstance(result, list):

                        for msg in result:
                            track_message(msg)

                    else:

                        track_message(result)

                except Exception as error:

                    print(
                        f"⚠️ {name} tracking error: {error}"
                    )

                return result

            return wrapper

        setattr(
            bot,
            method_name,
            make_wrapper(
                original_method,
                method_name
            )
        )

    print("✅ CLEAN MEMORY TRACKER READY")


# =========================================================
# REGISTER CLEAN
# =========================================================

def register_clean(bot):

    print("✅ CLEAN SYSTEM REGISTERED")

    # Message tracker install
    install_message_tracker(bot)


    # =====================================================
    # /clean COMMAND
    # =====================================================

    @bot.message_handler(commands=["clean"])
    def clean_command(message):

        print(
            f"🔥 /clean received | "
            f"Chat: {message.chat.id} | "
            f"User: {message.from_user.id}"
        )

        # =================================================
        # GROUP ONLY
        # =================================================

        if message.chat.type not in [
            "group",
            "supergroup"
        ]:
            return

        # =================================================
        # ADMIN ONLY
        # =================================================

        if message.from_user.id not in ADMIN_IDS:
            return

        chat_id = message.chat.id

        # =================================================
        # SAVE /CLEAN MESSAGE
        # =================================================

        track_message(message)

        # =================================================
        # CLEAN START MESSAGE
        # =================================================

        start_message = bot.send_message(
            chat_id,
            (
                "🧹 <b>CLEAN PROCESS STARTED</b>\n\n"
                "👥 Non-admin members remove kiye ja rahe hain.\n"
                "🗑️ Group ke tracked messages clear kiye ja rahe hain.\n"
                "🤖 Bot ke messages bhi clear kiye jayenge.\n"
                "🔗 Purana invite link revoke karke "
                "fresh link generate kiya jayega.\n\n"
                "⏳ <b>Please wait...</b>"
            ),
            parse_mode="HTML"
        )

        track_message(start_message)


        # =================================================
        # GET GROUP ADMINS
        # =================================================

        try:

            administrators = bot.get_chat_administrators(
                chat_id
            )

            admin_ids = {
                admin.user.id
                for admin in administrators
            }

        except Exception as error:

            print(
                f"❌ Admin list error: {error}"
            )

            return


        # =================================================
        # REMOVE NON-ADMINS
        # =================================================

        removed = 0

        users = tracked_users.get(
            chat_id,
            set()
        ).copy()

        for user_id in users:

            if user_id in admin_ids:
                continue

            try:

                # Temporary ban
                bot.ban_chat_member(
                    chat_id,
                    user_id
                )

                # Immediately unban
                # User permanently banned nahi rahega
                bot.unban_chat_member(
                    chat_id,
                    user_id,
                    only_if_banned=True
                )

                removed += 1

            except Exception as error:

                print(
                    f"❌ Remove user "
                    f"{user_id} error: {error}"
                )


        # =================================================
        # DELETE ALL TRACKED MESSAGES
        # =================================================

        deleted = 0

        messages = tracked_messages.get(
            chat_id,
            set()
        ).copy()

        # /clean message
        messages.add(
            message.message_id
        )

        # CLEAN STARTED message
        messages.add(
            start_message.message_id
        )

        # Previous new-link message
        old_link_message_id = managed_link_messages.get(
            chat_id
        )

        if old_link_message_id:

            messages.add(
                old_link_message_id
            )


        # Delete every tracked message
        for message_id in messages:

            try:

                bot.delete_message(
                    chat_id,
                    message_id
                )

                deleted += 1

            except Exception as error:

                print(
                    f"⚠️ Delete message "
                    f"{message_id} failed: {error}"
                )


        # =================================================
        # OLD INVITE LINK
        # =================================================

        old_link = managed_invite_links.get(
            chat_id
        )

        old_link_revoked = False

        if old_link:

            try:

                bot.revoke_chat_invite_link(
                    chat_id,
                    old_link
                )

                old_link_revoked = True

                print(
                    "✅ Old invite link revoked."
                )

            except Exception as error:

                print(
                    f"⚠️ Old invite revoke error: {error}"
                )


        # =================================================
        # CREATE NEW INVITE LINK
        # =================================================

        new_link = None

        try:

            invite = bot.create_chat_invite_link(
                chat_id
            )

            new_link = invite.invite_link

            managed_invite_links[
                chat_id
            ] = new_link

            print(
                "✅ New invite link created."
            )

        except Exception as error:

            print(
                f"❌ New invite link error: {error}"
            )


        # =================================================
        # RESET OLD TRACKING
        # =================================================

        tracked_messages.pop(
            chat_id,
            None
        )

        tracked_users.pop(
            chat_id,
            None
        )

        # Old link message ka record remove
        managed_link_messages.pop(
            chat_id,
            None
        )


        # =================================================
        # CLEAN COMPLETED MESSAGE
        # =================================================

        result = (
            "✅ <b>CLEAN COMPLETED</b>\n\n"
            f"👥 Members removed: <b>{removed}</b>\n"
            f"🧹 Messages deleted: <b>{deleted}</b>\n"
        )

        if old_link_revoked:

            result += (
                "🔒 Old invite link: <b>Revoked</b>\n"
            )

        else:

            result += (
                "⚠️ Old invite link: <b>Not found</b>\n"
            )

        if new_link:

            result += (
                "🔗 New invite link: <b>Generated</b>"
            )

        else:

            result += (
                "❌ New invite link: <b>Failed</b>"
            )


        result_message = bot.send_message(
            chat_id,
            result,
            parse_mode="HTML"
        )


        # =================================================
        # NEW LINK — SEPARATE MESSAGE
        # =================================================

        if new_link:

            new_link_message = bot.send_message(
                chat_id,
                new_link
            )

            # Is link message ko next /clean ke liye save karo
            managed_link_messages[
                chat_id
            ] = new_link_message.message_id

            # New link message ko tracking mein bhi rakho
            track_message(
                new_link_message
            )

        else:

            error_message = bot.send_message(
                chat_id,
                "❌ New invite link generate nahi ho paya."
            )

            track_message(
                error_message
            )


        print(
            f"✅ CLEAN COMPLETED | "
            f"Chat={chat_id} | "
            f"Removed={removed} | "
            f"Deleted={deleted}"
        )
