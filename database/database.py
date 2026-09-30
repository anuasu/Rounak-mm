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
            user_1_id,
            user_2_id,
            deal_amount,
            mm_fee,
            total_received,
            holding_amount,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
    """, (
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

    # --------------------------------------
    # Deal information
    # --------------------------------------

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

    # --------------------------------------
    # Mark completed
    # --------------------------------------

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

    # --------------------------------------
    # User 1 update
    # --------------------------------------

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

    # --------------------------------------
    # User 2 update
    # --------------------------------------

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

def update_payment(deal_id, total_received):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE deals
        SET total_received = ?
        WHERE deal_id = ?
    """, (
        total_received,
        deal_id
    ))

    connection.commit()
    connection.close()
