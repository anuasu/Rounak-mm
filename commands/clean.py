from config import ADMIN_IDS


# ==========================================
# TEMPORARY MEMORY
# ==========================================

tracked_messages = {}
tracked_users = {}
managed_invite_links = {}


# ==========================================
# REGISTER CLEAN SYSTEM
# ==========================================

def register_clean(bot):

    print("✅ CLEAN SYSTEM REGISTERED")

    # ======================================
    # TRACK GROUP MESSAGES
    # ======================================

    @bot.message_handler(
        func=lambda message:
            message.chat.type in ["group", "supergroup"]
            and not (
                message.text
                and message.text.lower().strip() == "/clean"
            )
    )
    def track_group_messages(message):

        chat_id = message.chat.id

        # Track message
        tracked_messages.setdefault(
            chat_id,
            set()
        ).add(message.message_id)

        # Track user
        if message.from_user:

            tracked_users.setdefault(
                chat_id,
                set()
            ).add(message.from_user.id)


    # ======================================
    # TRACK NEW MEMBERS
    # ======================================

    @bot.message_handler(
        content_types=["new_chat_members"]
    )
    def track_new_members(message):

        if message.chat.type not in [
            "group",
            "supergroup"
        ]:
            return

        chat_id = message.chat.id

        tracked_messages.setdefault(
            chat_id,
            set()
        ).add(message.message_id)

        for member in message.new_chat_members:

            tracked_users.setdefault(
                chat_id,
                set()
            ).add(member.id)


    # ======================================
    # /clean COMMAND
    # ======================================

    @bot.message_handler(commands=["clean"])
    def clean_command(message):

        print(
            f"🔥 /clean received | "
            f"Chat: {message.chat.id} | "
            f"User: {message.from_user.id}"
        )

        # ==================================
        # GROUP ONLY
        # ==================================

        if message.chat.type not in [
            "group",
            "supergroup"
        ]:
            return

        # ==================================
        # ADMIN ONLY
        # ==================================

        if message.from_user.id not in ADMIN_IDS:
            return

        chat_id = message.chat.id


        # ==================================
        # CLEAN START MESSAGE
        # ==================================

        start_message = bot.reply_to(
            message,
            (
                "🧹 <b>CLEAN PROCESS STARTED</b>\n\n"
                "👥 Non-admin members remove kiye ja rahe hain.\n"
                "🗑️ Bot ke active session ke tracked messages clear kiye ja rahe hain.\n"
                "🔗 Existing invite link revoke karke fresh link generate kiya jayega.\n\n"
                "⏳ Please wait..."
            ),
            parse_mode="HTML"
        )


        # ==================================
        # GET GROUP ADMINS
        # ==================================

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

            bot.send_message(
                chat_id,
                "❌ Group admins ki list get nahi ho paayi."
            )

            return


        # ==================================
        # REMOVE TRACKED NON-ADMINS
        # ==================================

        removed = 0

        users = tracked_users.get(
            chat_id,
            set()
        ).copy()

        for user_id in users:

            # Admin ko touch nahi karna
            if user_id in admin_ids:
                continue

            try:

                # User ko group se remove karo
                bot.ban_chat_member(
                    chat_id,
                    user_id
                )

                # Immediately unban
                # Isse permanent ban nahi rahega
                bot.unban_chat_member(
                    chat_id,
                    user_id,
                    only_if_banned=True
                )

                removed += 1

            except Exception as error:

                print(
                    f"❌ Remove user {user_id} error: {error}"
                )


        # ==================================
        # DELETE TRACKED MESSAGES
        # ==================================

        deleted = 0

        messages = tracked_messages.get(
            chat_id,
            set()
        ).copy()

        for message_id in messages:

            try:

                bot.delete_message(
                    chat_id,
                    message_id
                )

                deleted += 1

            except Exception as error:

                print(
                    f"❌ Delete message {message_id} error: {error}"
                )


        # ==================================
        # GET OLD INVITE LINK
        # ==================================

        old_link = managed_invite_links.get(
            chat_id
        )

        # Agar memory mein link nahi hai,
        # to Telegram se primary invite link lene ki koshish
        if not old_link:

            try:

                chat_info = bot.get_chat(
                    chat_id
                )

                old_link = getattr(
                    chat_info,
                    "invite_link",
                    None
                )

            except Exception as error:

                print(
                    f"⚠️ Existing invite link get error: {error}"
                )


        # ==================================
        # REVOKE OLD INVITE LINK
        # ==================================

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
                    f"⚠️ Old invite link revoke error: {error}"
                )

        else:

            print(
                "⚠️ No old invite link available to revoke."
            )


        # ==================================
        # CREATE NEW INVITE LINK
        # ==================================

        new_link = None

        try:

            invite = bot.create_chat_invite_link(
                chat_id
            )

            new_link = invite.invite_link

            # New link ko memory mein save karo
            managed_invite_links[chat_id] = new_link

            print(
                f"✅ New invite link created: {new_link}"
            )

        except Exception as error:

            print(
                f"❌ New invite link error: {error}"
            )


        # ==================================
        # DELETE CLEAN START MESSAGE
        # ==================================

        try:

            bot.delete_message(
                chat_id,
                start_message.message_id
            )

        except Exception as error:

            print(
                f"⚠️ Start message delete error: {error}"
            )


        # ==================================
        # DELETE /clean COMMAND
        # ==================================

        try:

            bot.delete_message(
                chat_id,
                message.message_id
            )

        except Exception as error:

            print(
                f"⚠️ /clean message delete error: {error}"
            )


        # ==================================
        # CLEAR TEMPORARY MEMORY
        # ==================================

        tracked_messages.pop(
            chat_id,
            None
        )

        tracked_users.pop(
            chat_id,
            None
        )


        # ==================================
        # CLEAN RESULT
        # ==================================

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
                "⚠️ Old invite link: <b>Could not revoke</b>\n"
            )

        if new_link:

            result += (
                "🔗 New invite link: <b>Generated</b>"
            )

        else:

            result += (
                "❌ New invite link: <b>Failed</b>"
            )


        bot.send_message(
            chat_id,
            result,
            parse_mode="HTML"
        )


        # ==================================
        # SEND ONLY NEW LINK
        # ==================================

        if new_link:

            bot.send_message(
                chat_id,
                new_link
            )
