# ==========================================
# COMMAND UTILS
# ==========================================


def normalize_dot_command(text):
    """
    Normalize dot commands.

    Supports:
    .payment 500
    . payment 500

    .deal
    . deal

    .hold 100
    . hold 100

    .voucher 500
    . voucher 500

    .form
    . form

    .QR 500
    . QR 500

    Normal non-dot messages remain unchanged.
    """

    if not text:
        return text

    text = text.strip()

    # --------------------------------------
    # DOT COMMAND
    # --------------------------------------

    if text.startswith("."):

        # Dot ke baad jitne bhi spaces hain
        # unko remove kar do.
        #
        # ". payment 500"
        # becomes
        # ".payment 500"

        text = "." + text[1:].lstrip()

    return text


# ==========================================
# BACKWARD COMPATIBILITY
# ==========================================

def normalize_command(text):
    """
    Old function name support.

    Agar kisi purani command file mein
    normalize_command() use ho raha hai,
    to woh bhi properly kaam karega.
    """

    return normalize_dot_command(text)


# ==========================================
# GET COMMAND NAME
# ==========================================

def get_command_name(text):
    """
    Examples:

    .payment 500
    -> payment

    . payment 500
    -> payment

    .deal
    -> deal

    . deal
    -> deal
    """

    if not text:
        return None

    text = normalize_dot_command(text)

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
    Deletes user's dot-command message
    after the command is processed.
    """

    try:

        if not message:
            return

        # Sirf groups/supergroups mein
        # command delete karega.
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

        # Bot ke paas delete permission na ho
        # to bot crash nahi karega.
        print(
            f"⚠️ Command delete error: {error}"
        )
