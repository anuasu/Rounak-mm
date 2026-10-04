# ==========================================
# COMMAND UTILS
# ==========================================


def normalize_command(text):
    """
    Normalizes dot commands.

    Examples:

    .payment 500
    -> .payment 500

    . payment 500
    -> .payment 500

    .   payment 500
    -> .payment 500

    .deal
    -> .deal

    . deal
    -> .deal

    Normal text remains unchanged.
    """

    if not text:
        return text

    text = text.strip()

    # --------------------------------------
    # ONLY DOT COMMANDS
    # --------------------------------------

    if not text.startswith("."):
        return text

    # --------------------------------------
    # REMOVE SPACES AFTER DOT
    # --------------------------------------

    text = "." + text[1:].lstrip()

    return text


# ==========================================
# GET COMMAND NAME
# ==========================================

def get_command_name(text):
    """
    Returns command name without dot.

    Examples:

    .payment 500
    -> payment

    . payment 500
    -> payment

    .   payment 500
    -> payment

    .deal
    -> deal

    Normal text
    -> None
    """

    if not text:
        return None

    text = normalize_command(text)

    if not text.startswith("."):
        return None

    parts = text.split()

    if not parts:
        return None

    command = parts[0]

    if not command.startswith("."):
        return None

    return command[1:].lower()


# ==========================================
# GET NORMALIZED TEXT
# ==========================================

def get_normalized_text(text):
    """
    Returns the complete normalized command text.

    Examples:

    . payment 500
    -> .payment 500

    .   hold    100
    -> .hold 100

    .deal
    -> .deal
    """

    return normalize_command(text)


# ==========================================
# CHECK DOT COMMAND
# ==========================================

def is_dot_command(text):
    """
    Checks whether the message is a dot command.

    Examples:

    .deal       -> True
    . payment   -> True
    .hold 100   -> True

    hello       -> False
    /admin      -> False
    """

    if not text:
        return False

    text = text.strip()

    return text.startswith(".")


# ==========================================
# DELETE COMMAND MESSAGE
# ==========================================

def delete_command_message(bot, message):
    """
    Deletes the user's dot-command message.

    Works only in groups/supergroups.

    If Telegram doesn't allow deletion,
    the error is safely ignored.
    """

    try:

        if not message:
            return

        # ----------------------------------
        # ONLY GROUP / SUPERGROUP
        # ----------------------------------

        if message.chat.type not in [
            "group",
            "supergroup"
        ]:
            return

        # ----------------------------------
        # DELETE USER COMMAND
        # ----------------------------------

        bot.delete_message(
            message.chat.id,
            message.message_id
        )

    except Exception as error:

        print(
            f"⚠️ Command delete error: {error}"
        )


# ==========================================
# PROCESS DOT COMMAND
# ==========================================

def prepare_command(text):
    """
    Utility for command handlers.

    Returns:

    {
        "is_command": True,
        "command": "payment",
        "text": ".payment 500",
        "parts": [".payment", "500"]
    }

    For normal messages:

    {
        "is_command": False,
        "command": None,
        "text": original_text,
        "parts": [...]
    }
    """

    if not text:

        return {
            "is_command": False,
            "command": None,
            "text": text,
            "parts": []
        }

    normalized = normalize_command(text)

    if not normalized.startswith("."):

        return {
            "is_command": False,
            "command": None,
            "text": normalized,
            "parts": normalized.split()
        }

    parts = normalized.split()

    if not parts:

        return {
            "is_command": False,
            "command": None,
            "text": normalized,
            "parts": []
        }

    command = parts[0][1:].lower()

    return {
        "is_command": True,
        "command": command,
        "text": normalized,
        "parts": parts
    }
