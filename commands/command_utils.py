# ==========================================
# COMMAND UTILS
# ==========================================

def normalize_command(text):
    """
    Converts:
    . payment  -> .payment
    . deal     -> .deal
    . hold     -> .hold

    Normal commands remain unchanged.
    """

    if not text:
        return text

    text = text.strip()

    # Dot command ke baad extra spaces remove
    if text.startswith("."):

        # "." ke baad ke spaces remove
        text = "." + text[1:].lstrip()

    return text


# ==========================================
# GET COMMAND NAME
# ==========================================

def get_command_name(text):
    """
    Example:
    .payment 500 -> payment
    . payment 500 -> payment
    .deal -> deal
    """

    if not text:
        return None

    text = normalize_command(text)

    if not text.startswith("."):
        return None

    parts = text.split()

    if not parts:
        return None

    return parts[0][1:].lower()


# ==========================================
# DELETE COMMAND MESSAGE
# ==========================================

def delete_command_message(bot, message):
    """
    Deletes the user's dot-command message.
    """

    try:

        if not message:
            return

        if message.chat.type not in [
            "group",
            "supergroup"
        ]:
            return

        bot.delete_message(
            message.chat.id,
            message.message_id
        )

    except Exception as error:

        print(
            f"⚠️ Command delete error: {error}"
        )
