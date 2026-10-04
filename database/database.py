import sqlite3
from datetime import datetime
from config import DATABASE_FILE


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_connection():
    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row
    return connection


# ==========================================
# DATABASE INITIALIZATION
# ==========================================

def init_database():

    connection = get_connection()
    cursor = connection.cursor()

    # ======================================
    # USERS
    # ======================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER PRIMARY KEY,
            first_name TEXT,
            username TEXT,
            completed_deals INTEGER DEFAULT 0,
            total_deal_amount REAL DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )
    """)

    # ======================================
    # DEALS
    # ======================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deals (
            deal_id INTEGER PRIMARY KEY AUTOINCREMENT,

            group_chat_id INTEGER,

            user_1_id INTEGER,
            user_2_id INTEGER,

            deal_amount REAL DEFAULT 0,
            mm_fee REAL DEFAULT 0,
            total_received REAL DEFAULT 0,
            holding_amount REAL DEFAULT 0,

            status TEXT DEFAULT 'pending',

            created_at TEXT,
            completed_at TEXT
        )
    """)

    # ======================================
    # MM FEE SETTINGS
    # ======================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mm_fee_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            image_file_id TEXT
        )
    """)

    # ======================================
    # QR SETTINGS
    # ======================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS qr_settings (
            qr_number INTEGER PRIMARY KEY,
            image_file_id TEXT,
            upi_id TEXT DEFAULT NULL
        )
    """)

    # ======================================
    # LEADERBOARD RESTORE STATS
    # ======================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leaderboard_stats (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            total_deals INTEGER DEFAULT 0,
            total_amount REAL DEFAULT 0
        )
    """)

    cursor.execute("""
        INSERT OR IGNORE INTO leaderboard_stats (
            id,
            total_deals,
            total_amount
        )
        VALUES (1, 0, 0)
    """)

    # ======================================
    # QR DATABASE MIGRATION
    # ======================================

    # Agar purane database mein qr_settings
    # table already hai aur upi_id column nahi hai,
    # to automatically column add ho jayega.

    cursor.execute("""
        PRAGMA table_info(qr_settings)
    """)

    columns = [
        row["name"]
        for row in cursor.fetchall()
    ]

    if "upi_id" not in columns:

        cursor.execute("""
            ALTER TABLE qr_settings
            ADD COLUMN upi_id TEXT DEFAULT NULL
        """)

    # ======================================
    # SAVE + CLOSE
    # ======================================

    connection.commit()
    connection.close()


# ==========================================
# SAVE / UPDATE USER
# ==========================================

def save_user(chat_id, first_name="", username=""):

    connection = get_connection()
    cursor = connection.cursor()

    now = datetime.now().isoformat()

    cursor.execute("""
        INSERT INTO users (
            chat_id,
            first_name,
            username,
            completed_deals,
            total_deal_amount,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, 0, 0, ?, ?)

        ON CONFLICT(chat_id)
        DO UPDATE SET
            first_name = excluded.first_name,
            username = excluded.username,
            updated_at = excluded.updated_at
    """, (
        chat_id,
        first_name,
        username,
        now,
        now
    ))

    connection.commit()
    connection.close()


# ==========================================
# GET USER
# ==========================================

def get_user(chat_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM users
        WHERE chat_id = ?
    """, (chat_id,))

    user = cursor.fetchone()

    connection.close()

    return user


# ==========================================
# CREATE DEAL
# ==========================================

def create_deal(
    group_chat_id,
    user_1_id,
    user_2_id,
    deal_amount=0,
    mm_fee=0,
    total_received=0,
    holding_amount=0
):

    connection = get_connection()
    cursor = connection.cursor()

    now = datetime.now().isoformat()

    cursor.execute("""
        INSERT INTO deals (
            group_chat_id,
            user_1_id,
            user_2_id,
            deal_amount,
            mm_fee,
            total_received,
            holding_amount,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
    """, (
        group_chat_id,
        user_1_id,
        user_2_id,
        deal_amount,
        mm_fee,
        total_received,
        holding_amount,
        now
    ))

    deal_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return deal_id


# ==========================================
# COMPLETE DEAL
# ==========================================

def complete_deal(deal_id):

    connection = get_connection()
    cursor = connection.cursor()

    now = datetime.now().isoformat()

    cursor.execute("""
        SELECT *
        FROM deals
        WHERE deal_id = ?
    """, (deal_id,))

    deal = cursor.fetchone()

    if not deal:
        connection.close()
        return False

    if deal["status"] == "completed":
        connection.close()
        return False

    cursor.execute("""
        UPDATE deals
        SET
            status = 'completed',
            completed_at = ?
        WHERE deal_id = ?
    """, (
        now,
        deal_id
    ))

    cursor.execute("""
        UPDATE leaderboard_stats
        SET
            total_deals = total_deals + 1,
            total_amount = total_amount + ?
        WHERE id = 1
    """, (
        deal["deal_amount"],
    ))

    cursor.execute("""
        UPDATE users
        SET
            completed_deals = completed_deals + 1,
            total_deal_amount = total_deal_amount + ?,
            updated_at = ?
        WHERE chat_id = ?
    """, (
        deal["deal_amount"],
        now,
        deal["user_1_id"]
    ))

    cursor.execute("""
        UPDATE users
        SET
            completed_deals = completed_deals + 1,
            total_deal_amount = total_deal_amount + ?,
            updated_at = ?
        WHERE chat_id = ?
    """, (
        deal["deal_amount"],
        now,
        deal["user_2_id"]
    ))

    connection.commit()
    connection.close()

    return True


# ==========================================
# LEADERBOARD
# ==========================================

def get_leaderboard(limit=20):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            chat_id,
            first_name,
            username,
            completed_deals,
            total_deal_amount

        FROM users

        WHERE completed_deals > 0

        ORDER BY
            completed_deals DESC,
            total_deal_amount DESC

        LIMIT ?
    """, (limit,))

    users = cursor.fetchall()

    connection.close()

    return users


# ==========================================
# TOTAL USER DEALS
# ==========================================

def get_total_user_deals():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            COALESCE(SUM(completed_deals), 0)
        FROM users
    """)

    total = cursor.fetchone()[0]

    connection.close()

    return total


# ==========================================
# GET USER DEAL HISTORY
# ==========================================

def get_user_deals(chat_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM deals
        WHERE user_1_id = ?
           OR user_2_id = ?
        ORDER BY deal_id DESC
    """, (
        chat_id,
        chat_id
    ))

    deals = cursor.fetchall()

    connection.close()

    return deals


# ==========================================
# UPDATE HOLDING
# ==========================================

def update_holding(deal_id, holding_amount):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE deals
        SET holding_amount = ?
        WHERE deal_id = ?
    """, (
        holding_amount,
        deal_id
    ))

    connection.commit()
    connection.close()


# ==========================================
# UPDATE PAYMENT
# ==========================================

def update_payment(deal_id, amount):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE deals
        SET
            deal_amount = ?,
            total_received = ?
        WHERE deal_id = ?
    """, (
        amount,
        amount,
        deal_id
    ))

    connection.commit()
    connection.close()


# ==========================================
# RAUNAK MM TOTAL STATS
# ==========================================

def get_mm_stats():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            total_deals,
            total_amount
        FROM leaderboard_stats
        WHERE id = 1
    """)

    stats = cursor.fetchone()

    connection.close()

    return stats


# ==========================================
# SEARCH USER
# ==========================================

def search_user(chat_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            chat_id,
            first_name,
            username,
            completed_deals,
            total_deal_amount
        FROM users
        WHERE chat_id = ?
    """, (chat_id,))

    user = cursor.fetchone()

    connection.close()

    return user


# ==========================================
# GET ACTIVE DEAL FOR GROUP
# ==========================================

def get_active_deal(group_chat_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM deals
        WHERE group_chat_id = ?
        AND status = 'pending'
        ORDER BY deal_id DESC
        LIMIT 1
    """, (group_chat_id,))

    deal = cursor.fetchone()

    connection.close()

    return deal


# ==========================================
# REMOVE ACTIVE DEAL
# ==========================================

def remove_deal(group_chat_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT deal_id
        FROM deals
        WHERE group_chat_id = ?
        AND status = 'pending'
        ORDER BY deal_id DESC
        LIMIT 1
    """, (group_chat_id,))

    deal = cursor.fetchone()

    if not deal:
        connection.close()
        return None

    deal_id = deal["deal_id"]

    cursor.execute("""
        DELETE FROM deals
        WHERE deal_id = ?
    """, (deal_id,))

    connection.commit()
    connection.close()

    return deal_id


# ==========================================
# GET MM FEE IMAGE
# ==========================================

def get_mm_fee_image():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT image_file_id
        FROM mm_fee_settings
        WHERE id = 1
    """)

    result = cursor.fetchone()

    connection.close()

    if result:
        return result["image_file_id"]

    return None


# ==========================================
# SET MM FEE IMAGE
# ==========================================

def set_mm_fee_image(image_file_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO mm_fee_settings (
            id,
            image_file_id
        )
        VALUES (1, ?)

        ON CONFLICT(id)
        DO UPDATE SET
            image_file_id = excluded.image_file_id
    """, (
        image_file_id,
    ))

    connection.commit()
    connection.close()


# ==========================================
# SET QR IMAGE
# ==========================================

def set_qr(qr_number, image_file_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO qr_settings (
            qr_number,
            image_file_id
        )
        VALUES (?, ?)

        ON CONFLICT(qr_number)
        DO UPDATE SET
            image_file_id = excluded.image_file_id
    """, (
        qr_number,
        image_file_id
    ))

    connection.commit()
    connection.close()


# ==========================================
# GET QR IMAGE
# ==========================================

def get_qr(qr_number):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT image_file_id
        FROM qr_settings
        WHERE qr_number = ?
    """, (
        qr_number,
    ))

    result = cursor.fetchone()

    connection.close()

    if result:
        return result["image_file_id"]

    return None


# ==========================================
# SET QR UPI
# ==========================================

def set_qr_upi(qr_number, upi_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO qr_settings (
            qr_number,
            image_file_id,
            upi_id
        )
        VALUES (?, NULL, ?)

        ON CONFLICT(qr_number)
        DO UPDATE SET
            upi_id = excluded.upi_id
    """, (
        qr_number,
        upi_id
    ))

    connection.commit()
    connection.close()


# ==========================================
# GET QR UPI
# ==========================================

def get_qr_upi(qr_number):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT upi_id
        FROM qr_settings
        WHERE qr_number = ?
    """, (
        qr_number,
    ))

    result = cursor.fetchone()

    connection.close()

    if result:
        return result["upi_id"]

    return None


# ==========================================
# SET QR IMAGE + UPI TOGETHER
# ==========================================

def set_qr_details(
    qr_number,
    image_file_id,
    upi_id=None
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO qr_settings (
            qr_number,
            image_file_id,
            upi_id
        )
        VALUES (?, ?, ?)

        ON CONFLICT(qr_number)
        DO UPDATE SET
            image_file_id = excluded.image_file_id,
            upi_id = excluded.upi_id
    """, (
        qr_number,
        image_file_id,
        upi_id
    ))

    connection.commit()
    connection.close()


# ==========================================
# GET COMPLETE QR DETAILS
# ==========================================

def get_qr_details(qr_number):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            qr_number,
            image_file_id,
            upi_id
        FROM qr_settings
        WHERE qr_number = ?
    """, (
        qr_number,
    ))

    result = cursor.fetchone()

    connection.close()

    return result


# ==========================================
# GET BACKUP DATA
# ==========================================

def get_backup_data():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            COUNT(*) AS total_deals,
            COALESCE(SUM(deal_amount), 0) AS total_amount
        FROM deals
        WHERE status = 'completed'
    """)

    mm_stats = cursor.fetchone()

    cursor.execute("""
        SELECT
            chat_id,
            first_name,
            username,
            completed_deals,
            total_deal_amount
        FROM users
        WHERE completed_deals > 0
        ORDER BY
            completed_deals DESC,
            total_deal_amount DESC
    """)

    users = cursor.fetchall()

    user_data = []

    for user in users:

        user_data.append({
            "user_id": user["chat_id"],
            "first_name": user["first_name"] or "",
            "username": user["username"] or "",
            "deals": user["completed_deals"] or 0,
            "amount": user["total_deal_amount"] or 0
        })

    connection.close()

    return {
        "raunak_mm": {
            "total_deals": mm_stats["total_deals"] or 0,
            "total_amount": mm_stats["total_amount"] or 0
        },

        "users": user_data
    }


# ==========================================
# RESTORE BACKUP DATA
# ==========================================

def restore_backup_data(backup_data):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # ==================================
        # RAUNAK MM STATS
        # ==================================

        raunak_data = backup_data.get(
            "raunak_mm",
            {}
        )

        total_deals = int(
            raunak_data.get(
                "total_deals",
                0
            )
        )

        total_amount = float(
            raunak_data.get(
                "total_amount",
                0
            )
        )

        cursor.execute("""
            UPDATE leaderboard_stats
            SET
                total_deals = ?,
                total_amount = ?
            WHERE id = 1
        """, (
            total_deals,
            total_amount
        ))

        # ==================================
        # USERS
        # ==================================

        users = backup_data.get(
            "users",
            []
        )

        for user in users:

            now = datetime.now().isoformat()

            cursor.execute("""
                INSERT INTO users (
                    chat_id,
                    first_name,
                    username,
                    completed_deals,
                    total_deal_amount,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)

                ON CONFLICT(chat_id)
                DO UPDATE SET
                    first_name = excluded.first_name,
                    username = excluded.username,
                    completed_deals = excluded.completed_deals,
                    total_deal_amount = excluded.total_deal_amount,
                    updated_at = excluded.updated_at
            """, (
                user["user_id"],
                user.get("first_name", ""),
                user.get("username", ""),
                user.get("deals", 0),
                user.get("amount", 0),
                now,
                now
            ))

        connection.commit()

        return True

    except Exception as error:

        connection.rollback()

        print(
            f"Restore error: {error}"
        )

        return False

    finally:

        connection.close()


    # ==========================================
# TOTAL USERS
# ==========================================

def get_total_users():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM users
    """)

    total = cursor.fetchone()[0]

    connection.close()

    return total


# ==========================================
# ACTIVE USERS — LAST 30 DAYS
# ==========================================

def get_active_users():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE updated_at >= datetime('now', '-30 days')
    """)

    active = cursor.fetchone()[0]

    connection.close()

    return active
