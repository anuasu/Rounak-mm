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
# CURRENT TIME
# ==========================================

def current_time():
    return datetime.now().isoformat()


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
            final_action TEXT DEFAULT NULL,

            created_at TEXT,
            completed_at TEXT,

            hold_at TEXT,
            release_at TEXT,
            refund_at TEXT
        )
    """)

    # ======================================
    # DEAL EVENTS
    # ======================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deal_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,

            deal_id INTEGER,
            group_chat_id INTEGER,

            event_type TEXT,

            user_id INTEGER,
            amount REAL DEFAULT 0,
            mm_fee REAL DEFAULT 0,

            event_time TEXT
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
    # LEADERBOARD STATS
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
    # SAFE MIGRATION — DEALS
    # ======================================

    cursor.execute("PRAGMA table_info(deals)")

    deal_columns = [
        row["name"]
        for row in cursor.fetchall()
    ]

    if "hold_at" not in deal_columns:
        cursor.execute("""
            ALTER TABLE deals
            ADD COLUMN hold_at TEXT
        """)

    if "release_at" not in deal_columns:
        cursor.execute("""
            ALTER TABLE deals
            ADD COLUMN release_at TEXT
        """)

    if "refund_at" not in deal_columns:
        cursor.execute("""
            ALTER TABLE deals
            ADD COLUMN refund_at TEXT
        """)

    if "final_action" not in deal_columns:
        cursor.execute("""
            ALTER TABLE deals
            ADD COLUMN final_action TEXT DEFAULT NULL
        """)

    # ======================================
    # SAFE MIGRATION — QR
    # ======================================

    cursor.execute("PRAGMA table_info(qr_settings)")

    qr_columns = [
        row["name"]
        for row in cursor.fetchall()
    ]

    if "upi_id" not in qr_columns:
        cursor.execute("""
            ALTER TABLE qr_settings
            ADD COLUMN upi_id TEXT DEFAULT NULL
        """)

    connection.commit()
    connection.close()


# ==========================================
# SAVE / UPDATE USER
# ==========================================

def save_user(chat_id, first_name="", username=""):

    connection = get_connection()
    cursor = connection.cursor()

    now = current_time()

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

    now = current_time()

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
            final_action,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', NULL, ?)
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

    cursor.execute("""
        INSERT INTO deal_events (
            deal_id,
            group_chat_id,
            event_type,
            user_id,
            amount,
            mm_fee,
            event_time
        )
        VALUES (?, ?, 'created', NULL, ?, ?, ?)
    """, (
        deal_id,
        group_chat_id,
        deal_amount,
        mm_fee,
        now
    ))

    connection.commit()
    connection.close()

    return deal_id


# ==========================================
# ADD DEAL EVENT
# ==========================================

def add_deal_event(
    deal_id,
    event_type,
    user_id=None,
    amount=0,
    mm_fee=0,
    group_chat_id=None
):

    connection = get_connection()
    cursor = connection.cursor()

    now = current_time()

    if group_chat_id is None:

        cursor.execute("""
            SELECT group_chat_id
            FROM deals
            WHERE deal_id = ?
        """, (deal_id,))

        deal = cursor.fetchone()

        if deal:
            group_chat_id = deal["group_chat_id"]

    cursor.execute("""
        INSERT INTO deal_events (
            deal_id,
            group_chat_id,
            event_type,
            user_id,
            amount,
            mm_fee,
            event_time
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        deal_id,
        group_chat_id,
        event_type,
        user_id,
        amount,
        mm_fee,
        now
    ))

    event_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return event_id


# ==========================================
# UPDATE HOLDING
# ==========================================

def update_holding(
    deal_id,
    holding_amount,
    mm_fee=0,
    received_amount=None
):

    connection = get_connection()
    cursor = connection.cursor()

    now = current_time()

    if received_amount is None:
        received_amount = holding_amount + mm_fee

    cursor.execute("""
        UPDATE deals
        SET
            holding_amount = ?,
            mm_fee = ?,
            total_received = ?,
            hold_at = ?
        WHERE deal_id = ?
        AND status = 'pending'
    """, (
        holding_amount,
        mm_fee,
        received_amount,
        now,
        deal_id
    ))

    if cursor.rowcount == 0:
        connection.close()
        return False

    cursor.execute("""
        SELECT group_chat_id
        FROM deals
        WHERE deal_id = ?
    """, (deal_id,))

    deal = cursor.fetchone()

    group_chat_id = (
        deal["group_chat_id"]
        if deal
        else None
    )

    cursor.execute("""
        INSERT INTO deal_events (
            deal_id,
            group_chat_id,
            event_type,
            user_id,
            amount,
            mm_fee,
            event_time
        )
        VALUES (?, ?, 'hold', NULL, ?, ?, ?)
    """, (
        deal_id,
        group_chat_id,
        holding_amount,
        mm_fee,
        now
    ))

    connection.commit()
    connection.close()

    return True


# ==========================================
# UPDATE PAYMENT
# ==========================================

def update_payment(deal_id, amount, mm_fee=0):

    connection = get_connection()
    cursor = connection.cursor()

    now = current_time()

    cursor.execute("""
        UPDATE deals
        SET
            deal_amount = ?,
            total_received = ?,
            mm_fee = ?
        WHERE deal_id = ?
        AND status = 'pending'
    """, (
        amount,
        amount,
        mm_fee,
        deal_id
    ))

    if cursor.rowcount == 0:
        connection.close()
        return False

    cursor.execute("""
        SELECT group_chat_id
        FROM deals
        WHERE deal_id = ?
    """, (deal_id,))

    deal = cursor.fetchone()

    group_chat_id = (
        deal["group_chat_id"]
        if deal
        else None
    )

    cursor.execute("""
        INSERT INTO deal_events (
            deal_id,
            group_chat_id,
            event_type,
            user_id,
            amount,
            mm_fee,
            event_time
        )
        VALUES (?, ?, 'payment', NULL, ?, ?, ?)
    """, (
        deal_id,
        group_chat_id,
        amount,
        mm_fee,
        now
    ))

    connection.commit()
    connection.close()

    return True


# ==========================================
# CHECK FINAL ACTION
# ==========================================

def can_complete_deal(deal_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            status,
            final_action
        FROM deals
        WHERE deal_id = ?
    """, (deal_id,))

    deal = cursor.fetchone()

    connection.close()

    if not deal:
        return False

    return (
        deal["status"] != "completed"
        and deal["final_action"] is None
    )


# ==========================================
# GET ACTIVE DEAL
# ==========================================

def get_active_deal(group_chat_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM deals
        WHERE group_chat_id = ?
        AND status = 'pending'
        AND final_action IS NULL
        ORDER BY deal_id DESC
        LIMIT 1
    """, (
        group_chat_id,
    ))

    deal = cursor.fetchone()

    connection.close()

    return deal


# ==========================================
# FINALIZE DEAL
# ==========================================

def finalize_deal(
    deal_id,
    action,
    user_amounts
):

    """
    action:
        release
        refund
        split

    user_amounts:
        {
            user_id: amount,
            user_id: amount
        }

    For release/refund:
        Both users can receive the same final amount.

    For split:
        Each user gets the exact amount supplied.
    """

    allowed_actions = {
        "release",
        "refund",
        "split"
    }

    if action not in allowed_actions:
        return False

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # ==================================
        # GET DEAL
        # ==================================

        cursor.execute("""
            SELECT *
            FROM deals
            WHERE deal_id = ?
        """, (deal_id,))

        deal = cursor.fetchone()

        if not deal:
            connection.close()
            return False

        # ==================================
        # ALREADY COMPLETED
        # ==================================

        if deal["status"] == "completed":
            connection.close()
            return False

        if deal["final_action"] is not None:
            connection.close()
            return False

        # ==================================
        # USERS
        # ==================================

        user_1_id = deal["user_1_id"]
        user_2_id = deal["user_2_id"]

        amount_1 = float(
            user_amounts.get(user_1_id, 0)
        )

        amount_2 = float(
            user_amounts.get(user_2_id, 0)
        )

        # ==================================
        # FINAL EVENT
        # ==================================

        now = current_time()

        if action == "release":

            cursor.execute("""
                INSERT INTO deal_events (
                    deal_id,
                    group_chat_id,
                    event_type,
                    user_id,
                    amount,
                    mm_fee,
                    event_time
                )
                VALUES (?, ?, 'release', ?, ?, 0, ?)
            """, (
                deal_id,
                deal["group_chat_id"],
                user_1_id,
                amount_1,
                now
            ))

            cursor.execute("""
                INSERT INTO deal_events (
                    deal_id,
                    group_chat_id,
                    event_type,
                    user_id,
                    amount,
                    mm_fee,
                    event_time
                )
                VALUES (?, ?, 'release', ?, ?, 0, ?)
            """, (
                deal_id,
                deal["group_chat_id"],
                user_2_id,
                amount_2,
                now
            ))

        elif action == "refund":

            cursor.execute("""
                INSERT INTO deal_events (
                    deal_id,
                    group_chat_id,
                    event_type,
                    user_id,
                    amount,
                    mm_fee,
                    event_time
                )
                VALUES (?, ?, 'refund', ?, ?, 0, ?)
            """, (
                deal_id,
                deal["group_chat_id"],
                user_1_id,
                amount_1,
                now
            ))

            cursor.execute("""
                INSERT INTO deal_events (
                    deal_id,
                    group_chat_id,
                    event_type,
                    user_id,
                    amount,
                    mm_fee,
                    event_time
                )
                VALUES (?, ?, 'refund', ?, ?, 0, ?)
            """, (
                deal_id,
                deal["group_chat_id"],
                user_2_id,
                amount_2,
                now
            ))

        elif action == "split":

            cursor.execute("""
                INSERT INTO deal_events (
                    deal_id,
                    group_chat_id,
                    event_type,
                    user_id,
                    amount,
                    mm_fee,
                    event_time
                )
                VALUES (?, ?, 'split_release', ?, ?, 0, ?)
            """, (
                deal_id,
                deal["group_chat_id"],
                user_1_id,
                amount_1,
                now
            ))

            cursor.execute("""
                INSERT INTO deal_events (
                    deal_id,
                    group_chat_id,
                    event_type,
                    user_id,
                    amount,
                    mm_fee,
                    event_time
                )
                VALUES (?, ?, 'split_refund', ?, ?, 0, ?)
            """, (
                deal_id,
                deal["group_chat_id"],
                user_2_id,
                amount_2,
                now
            ))

        # ==================================
        # UPDATE DEAL
        # ==================================

        cursor.execute("""
            UPDATE deals
            SET
                status = 'completed',
                final_action = ?,
                completed_at = ?,
                release_at = CASE
                    WHEN ? IN ('release', 'split')
                    THEN ?
                    ELSE release_at
                END,
                refund_at = CASE
                    WHEN ? IN ('refund', 'split')
                    THEN ?
                    ELSE refund_at
                END
            WHERE deal_id = ?
            AND status = 'pending'
            AND final_action IS NULL
        """, (
            action,
            now,
            action,
            now,
            action,
            now,
            deal_id
        ))

        if cursor.rowcount == 0:
            connection.rollback()
            connection.close()
            return False

        # ==================================
        # LEADERBOARD
        # ==================================

        cursor.execute("""
            UPDATE leaderboard_stats
            SET
                total_deals = total_deals + 1,
                total_amount = total_amount + ?
            WHERE id = 1
        """, (
            deal["deal_amount"],
        ))

        # ==================================
        # USER 1
        # ==================================

        cursor.execute("""
            UPDATE users
            SET
                completed_deals = completed_deals + 1,
                total_deal_amount = total_deal_amount + ?,
                updated_at = ?
            WHERE chat_id = ?
        """, (
            amount_1,
            now,
            user_1_id
        ))

        # ==================================
        # USER 2
        # ==================================

        cursor.execute("""
            UPDATE users
            SET
                completed_deals = completed_deals + 1,
                total_deal_amount = total_deal_amount + ?,
                updated_at = ?
            WHERE chat_id = ?
        """, (
            amount_2,
            now,
            user_2_id
        ))

        connection.commit()
        connection.close()

        return True

    except Exception as error:

        connection.rollback()
        connection.close()

        print(
            f"Finalize deal error: {error}"
        )

        return False


# ==========================================
# RELEASE TRANSACTION
# ==========================================

def record_release(
    deal_id,
    user_id,
    amount
):

    connection = get_connection()
    cursor = connection.cursor()

    try:

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

        now = current_time()

        cursor.execute("""
            INSERT INTO deal_events (
                deal_id,
                group_chat_id,
                event_type,
                user_id,
                amount,
                mm_fee,
                event_time
            )
            VALUES (?, ?, 'release', ?, ?, 0, ?)
        """, (
            deal_id,
            deal["group_chat_id"],
            user_id,
            amount,
            now
        ))

        cursor.execute("""
            UPDATE deals
            SET release_at = ?
            WHERE deal_id = ?
        """, (
            now,
            deal_id
        ))

        connection.commit()
        connection.close()

        return True

    except Exception as error:

        connection.rollback()
        connection.close()

        print(
            f"Release event error: {error}"
        )

        return False


# ==========================================
# REFUND TRANSACTION
# ==========================================

def record_refund(
    deal_id,
    user_id,
    amount
):

    connection = get_connection()
    cursor = connection.cursor()

    try:

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

        now = current_time()

        cursor.execute("""
            INSERT INTO deal_events (
                deal_id,
                group_chat_id,
                event_type,
                user_id,
                amount,
                mm_fee,
                event_time
            )
            VALUES (?, ?, 'refund', ?, ?, 0, ?)
        """, (
            deal_id,
            deal["group_chat_id"],
            user_id,
            amount,
            now
        ))

        cursor.execute("""
            UPDATE deals
            SET refund_at = ?
            WHERE deal_id = ?
        """, (
            now,
            deal_id
        ))

        connection.commit()
        connection.close()

        return True

    except Exception as error:

        connection.rollback()
        connection.close()

        print(
            f"Refund event error: {error}"
        )

        return False


# ==========================================
# SPLIT TRANSACTION
# ==========================================

def record_split(
    deal_id,
    refund_user_id,
    refund_amount,
    release_user_id,
    release_amount
):

    connection = get_connection()
    cursor = connection.cursor()

    try:

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

        now = current_time()

        # ==================================
        # REFUND SIDE
        # ==================================

        cursor.execute("""
            INSERT INTO deal_events (
                deal_id,
                group_chat_id,
                event_type,
                user_id,
                amount,
                mm_fee,
                event_time
            )
            VALUES (?, ?, 'split_refund', ?, ?, 0, ?)
        """, (
            deal_id,
            deal["group_chat_id"],
            refund_user_id,
            refund_amount,
            now
        ))

        # ==================================
        # RELEASE SIDE
        # ==================================

        cursor.execute("""
            INSERT INTO deal_events (
                deal_id,
                group_chat_id,
                event_type,
                user_id,
                amount,
                mm_fee,
                event_time
            )
            VALUES (?, ?, 'split_release', ?, ?, 0, ?)
        """, (
            deal_id,
            deal["group_chat_id"],
            release_user_id,
            release_amount,
            now
        ))

        # ==================================
        # MARK COMPLETED
        # ==================================

        cursor.execute("""
            UPDATE deals
            SET
                status = 'completed',
                final_action = 'split',
                completed_at = ?,
                refund_at = ?,
                release_at = ?
            WHERE deal_id = ?
            AND status = 'pending'
            AND final_action IS NULL
        """, (
            now,
            now,
            now,
            deal_id
        ))

        if cursor.rowcount == 0:
            connection.rollback()
            connection.close()
            return False

        # ==================================
        # LEADERBOARD
        # ==================================

        cursor.execute("""
            UPDATE leaderboard_stats
            SET
                total_deals = total_deals + 1,
                total_amount = total_amount + ?
            WHERE id = 1
        """, (
            deal["deal_amount"],
        ))

        # ==================================
        # REFUND USER
        # ==================================

        cursor.execute("""
            UPDATE users
            SET
                completed_deals = completed_deals + 1,
                total_deal_amount = total_deal_amount + ?,
                updated_at = ?
            WHERE chat_id = ?
        """, (
            refund_amount,
            now,
            refund_user_id
        ))

        # ==================================
        # RELEASE USER
        # ==================================

        cursor.execute("""
            UPDATE users
            SET
                completed_deals = completed_deals + 1,
                total_deal_amount = total_deal_amount + ?,
                updated_at = ?
            WHERE chat_id = ?
        """, (
            release_amount,
            now,
            release_user_id
        ))

        connection.commit()
        connection.close()

        return True

    except Exception as error:

        connection.rollback()
        connection.close()

        print(
            f"Split error: {error}"
        )

        return False


# ==========================================
# COMPLETE DEAL — LEGACY COMPATIBILITY
# ==========================================

def complete_deal(deal_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM deals
        WHERE deal_id = ?
    """, (deal_id,))

    deal = cursor.fetchone()

    connection.close()

    if not deal:
        return False

    if deal["status"] == "completed":
        return False

    amount = deal["deal_amount"]

    return finalize_deal(
        deal_id,
        "release",
        {
            deal["user_1_id"]: amount,
            deal["user_2_id"]: amount
        }
    )


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
# GET DEAL EVENTS
# ==========================================

def get_deal_events(deal_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM deal_events
        WHERE deal_id = ?
        ORDER BY event_id ASC
    """, (
        deal_id,
    ))

    events = cursor.fetchall()

    connection.close()

    return events


# ==========================================
# GET TODAY DEALS
# ==========================================

def get_today_deals():

    connection = get_connection()
    cursor = connection.cursor()

    today = datetime.now().strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT *
        FROM deals
        WHERE DATE(created_at) = ?
        ORDER BY deal_id ASC
    """, (
        today,
    ))

    deals = cursor.fetchall()

    connection.close()

    return deals


# ==========================================
# GET DEALS BY DATE
# ==========================================

def get_deals_by_date(date_text):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM deals
        WHERE DATE(created_at) = ?
        ORDER BY deal_id ASC
    """, (
        date_text,
    ))

    deals = cursor.fetchall()

    connection.close()

    return deals


# ==========================================
# GET EVENTS BY DATE
# ==========================================

def get_events_by_date(date_text):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM deal_events
        WHERE DATE(event_time) = ?
        ORDER BY event_id ASC
    """, (
        date_text,
    ))

    events = cursor.fetchall()

    connection.close()

    return events


# ==========================================
# DAILY SUMMARY
# ==========================================

def get_daily_summary(date_text=None):

    connection = get_connection()
    cursor = connection.cursor()

    if date_text is None:
        date_text = datetime.now().strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT COUNT(*)
        FROM deals
        WHERE DATE(created_at) = ?
    """, (
        date_text,
    ))

    total_deals = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(deal_amount), 0)
        FROM deals
        WHERE DATE(created_at) = ?
    """, (
        date_text,
    ))

    total_amount = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM deal_events
        WHERE DATE(event_time) = ?
        AND event_type = 'hold'
    """, (
        date_text,
    ))

    total_hold = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(mm_fee), 0)
        FROM deal_events
        WHERE DATE(event_time) = ?
        AND event_type = 'hold'
    """, (
        date_text,
    ))

    total_fee = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM deal_events
        WHERE DATE(event_time) = ?
        AND event_type IN (
            'release',
            'split_release'
        )
    """, (
        date_text,
    ))

    total_release = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM deal_events
        WHERE DATE(event_time) = ?
        AND event_type IN (
            'refund',
            'split_refund'
        )
    """, (
        date_text,
    ))

    total_refund = cursor.fetchone()[0]

    connection.close()

    return {
        "date": date_text,
        "total_deals": total_deals or 0,
        "total_amount": total_amount or 0,
        "total_hold": total_hold or 0,
        "total_fee": total_fee or 0,
        "total_release": total_release or 0,
        "total_refund": total_refund or 0
    }


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
        AND final_action IS NULL
        ORDER BY deal_id DESC
        LIMIT 1
    """, (
        group_chat_id,
    ))

    deal = cursor.fetchone()

    if not deal:
        connection.close()
        return None

    deal_id = deal["deal_id"]

    cursor.execute("""
        DELETE FROM deal_events
        WHERE deal_id = ?
    """, (
        deal_id,
    ))

    cursor.execute("""
        DELETE FROM deals
        WHERE deal_id = ?
    """, (
        deal_id,
    ))

    connection.commit()
    connection.close()

    return deal_id


# ==========================================
# MM FEE IMAGE
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
# QR IMAGE
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
# QR UPI
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
# QR DETAILS
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
# BACKUP DATA
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

    # ======================================
    # USERS
    # ======================================

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

    # ======================================
    # DEALS
    # ======================================

    cursor.execute("""
        SELECT *
        FROM deals
        ORDER BY deal_id ASC
    """)

    deals = cursor.fetchall()

    deal_data = []

    for deal in deals:

        deal_data.append({
            "deal_id": deal["deal_id"],
            "group_chat_id": deal["group_chat_id"],
            "user_1_id": deal["user_1_id"],
            "user_2_id": deal["user_2_id"],
            "deal_amount": deal["deal_amount"] or 0,
            "mm_fee": deal["mm_fee"] or 0,
            "total_received": deal["total_received"] or 0,
            "holding_amount": deal["holding_amount"] or 0,
            "status": deal["status"],
            "final_action": deal["final_action"],
            "created_at": deal["created_at"],
            "completed_at": deal["completed_at"],
            "hold_at": deal["hold_at"],
            "release_at": deal["release_at"],
            "refund_at": deal["refund_at"]
        })

    # ======================================
    # EVENTS
    # ======================================

    cursor.execute("""
        SELECT *
        FROM deal_events
        ORDER BY event_id ASC
    """)

    events = cursor.fetchall()

    event_data = []

    for event in events:

        event_data.append({
            "event_id": event["event_id"],
            "deal_id": event["deal_id"],
            "group_chat_id": event["group_chat_id"],
            "event_type": event["event_type"],
            "user_id": event["user_id"],
            "amount": event["amount"] or 0,
            "mm_fee": event["mm_fee"] or 0,
            "event_time": event["event_time"]
        })

    connection.close()

    return {
        "raunak_mm": {
            "total_deals": mm_stats["total_deals"] or 0,
            "total_amount": mm_stats["total_amount"] or 0
        },

        "users": user_data,

        "deals": deal_data,

        "deal_events": event_data
    }


# ==========================================
# RESTORE BACKUP DATA
# ==========================================

def restore_backup_data(backup_data):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # ==================================
        # RAUNAK STATS
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

            now = current_time()

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

        # ==================================
        # DEALS
        # ==================================

        for deal in backup_data.get("deals", []):

            cursor.execute("""
                INSERT OR REPLACE INTO deals (
                    deal_id,
                    group_chat_id,
                    user_1_id,
                    user_2_id,
                    deal_amount,
                    mm_fee,
                    total_received,
                    holding_amount,
                    status,
                    final_action,
                    created_at,
                    completed_at,
                    hold_at,
                    release_at,
                    refund_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                deal.get("deal_id"),
                deal.get("group_chat_id"),
                deal.get("user_1_id"),
                deal.get("user_2_id"),
                deal.get("deal_amount", 0),
                deal.get("mm_fee", 0),
                deal.get("total_received", 0),
                deal.get("holding_amount", 0),
                deal.get("status", "pending"),
                deal.get("final_action"),
                deal.get("created_at"),
                deal.get("completed_at"),
                deal.get("hold_at"),
                deal.get("release_at"),
                deal.get("refund_at")
            ))

        # ==================================
        # EVENTS
        # ==================================

        for event in backup_data.get("deal_events", []):

            cursor.execute("""
                INSERT OR REPLACE INTO deal_events (
                    event_id,
                    deal_id,
                    group_chat_id,
                    event_type,
                    user_id,
                    amount,
                    mm_fee,
                    event_time
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.get("event_id"),
                event.get("deal_id"),
                event.get("group_chat_id"),
                event.get("event_type"),
                event.get("user_id"),
                event.get("amount", 0),
                event.get("mm_fee", 0),
                event.get("event_time")
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
