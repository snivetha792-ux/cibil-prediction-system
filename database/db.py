import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "users.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def init_db():
    connection = get_connection()

    # Users table
    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Prediction history table
    connection.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            monthly_income REAL,
            employment_status TEXT,
            loan_amount REAL,
            emi REAL,
            existing_loans INTEGER,
            credit_utilization REAL,
            repayment_history REAL,
            delayed_payments INTEGER,
            outstanding_debt REAL,
            risk TEXT,
            confidence REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()


def create_user(name, email, password_hash):
    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO users (name, email, password)
            VALUES (?, ?, ?)
            """,
            (name, email, password_hash)
        )

        connection.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        connection.close()


def get_user_by_email(email):
    connection = get_connection()

    user = connection.execute(
        """
        SELECT * FROM users WHERE email = ?
        """,
        (email,)
    ).fetchone()

    connection.close()

    return user


def save_prediction(
    user_email,
    monthly_income,
    employment_status,
    loan_amount,
    emi,
    existing_loans,
    credit_utilization,
    repayment_history,
    delayed_payments,
    outstanding_debt,
    risk,
    confidence
):
    connection = get_connection()

    connection.execute(
        """
        INSERT INTO predictions (
            user_email,
            monthly_income,
            employment_status,
            loan_amount,
            emi,
            existing_loans,
            credit_utilization,
            repayment_history,
            delayed_payments,
            outstanding_debt,
            risk,
            confidence
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_email,
            monthly_income,
            employment_status,
            loan_amount,
            emi,
            existing_loans,
            credit_utilization,
            repayment_history,
            delayed_payments,
            outstanding_debt,
            risk,
            confidence
        )
    )

    connection.commit()
    connection.close()


def get_predictions_by_user(user_email):
    connection = get_connection()

    predictions = connection.execute(
        """
        SELECT *
        FROM predictions
        WHERE user_email = ?
        ORDER BY created_at DESC
        """,
        (user_email,)
    ).fetchall()

    connection.close()

    return predictions