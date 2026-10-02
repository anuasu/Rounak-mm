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

        # Message track
        tracked_messages.setdefault(
            chat_id,
            set()
        ).add(message.message_id)

        # User track
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

        # GROUP ONLY
        if message.chat.type not in [
            "group",
            "supergroup"
        ]:
            return

        # ADMIN ONLY
        if message.from_user.id not in ADMIN_IDS:
            return

        chat_id = message.chat.id

        # ==================================
        # START MESSAGE
        # ==================================

        bot.reply_to(
            message,
            (
                "🧹 <b>CLEAN STARTED</b>\n\n"
                "👥 Members remove ho rahe hain...\n"
                "🗑️ Messages clear ho rahe hain...\n"
                "🔗 New invite link generate hoga."
            ),
            parse_mode="HTML"
        )

        # ==================================
        # GET ADMINS
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
                "❌ Admin list get nahi ho paayi."
            )

            return


        # ==================================
        # REMOVE NON-ADMINS
        # ==================================

        removed = 0

        users = tracked_users.get(
            chat_id,
            set()
        ).copy()

        for user_id in users:

            if user_id in admin_ids:
                continue

            try:

                # Remove from group
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
        # CREATE NEW INVITE LINK
        # ==================================

        new_link = None

        try:

            old_link = managed_invite_links.get(
                chat_id
            )

            # Revoke previous bot-managed link
            if old_link:

                try:

                    bot.revoke_chat_invite_link(
                        chat_id,
                        old_link
                    )

                except Exception as error:

                    print(
                        f"⚠️ Old link revoke error: {error}"
                    )

            # Create new link
            invite = bot.create_chat_invite_link(
                chat_id
            )

            new_link = invite.invite_link

            managed_invite_links[chat_id] = new_link

        except Exception as error:

            print(
                f"❌ New invite link error: {error}"
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
        # RESULT
        # ==================================

        result = (
            "✅ <b>CLEAN COMPLETED</b>\n\n"
            f"👥 Members removed: <b>{removed}</b>\n"
            f"🧹 Messages deleted: <b>{deleted}</b>\n\n"
        )

        if new_link:

            result += (
                "🔗 <b>NEW GC LINK</b>\n\n"
                f"{new_link}"
            )

        else:

            result += (
                "❌ New invite link generate nahi ho paya."
            )

        bot.send_message(
            chat_id,
            result,
            parse_mode="HTML"
        )
