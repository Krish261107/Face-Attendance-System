"""
database.py — SQLite storage for batches, students, and attendance.
One file, no server. Every student gets marked Present or Absent each
session, so per-student attendance % can be computed directly.
"""

import sqlite3
import os
import numpy as np
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "attendance.db")
DEFAULT_BATCHES = ["Data Science", "Web Development", "C/C++"]


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""CREATE TABLE IF NOT EXISTS batches (
        batch_id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_name TEXT UNIQUE NOT NULL)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS students (
        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        roll_no TEXT,
        batch_id INTEGER NOT NULL REFERENCES batches(batch_id) ON DELETE CASCADE,
        encoding BLOB NOT NULL)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS attendance (
        student_id INTEGER NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
        batch_id INTEGER NOT NULL REFERENCES batches(batch_id) ON DELETE CASCADE,
        date TEXT NOT NULL,
        status TEXT NOT NULL,
        time TEXT NOT NULL,
        PRIMARY KEY (student_id, date))""")
    for name in DEFAULT_BATCHES:
        conn.execute("INSERT OR IGNORE INTO batches (batch_name) VALUES (?)", (name,))
    conn.commit()
    conn.close()


# --- Batches ---------------------------------------------------------------

def add_batch(name):
    name = name.strip()
    if not name:
        return False, "Batch name cannot be empty."
    conn = get_connection()
    try:
        conn.execute("INSERT INTO batches (batch_name) VALUES (?)", (name,))
        conn.commit()
        return True, f"Added batch '{name}'."
    except sqlite3.IntegrityError:
        return False, f"Batch '{name}' already exists."
    finally:
        conn.close()


def get_batches():
    conn = get_connection()
    rows = conn.execute("SELECT batch_id, batch_name FROM batches ORDER BY batch_name").fetchall()
    conn.close()
    return rows


def delete_batch(batch_id):
    conn = get_connection()
    conn.execute("DELETE FROM batches WHERE batch_id = ?", (batch_id,))
    conn.commit()
    conn.close()


# --- Students ----------------------------------------------------------------

def add_student(name, roll_no, batch_id, encoding):
    conn = get_connection()
    conn.execute(
        "INSERT INTO students (name, roll_no, batch_id, encoding) VALUES (?, ?, ?, ?)",
        (name.strip(), roll_no.strip(), batch_id, np.asarray(encoding, dtype=np.float64).tobytes()),
    )
    conn.commit()
    conn.close()
    return True, f"Registered '{name.strip()}'."


def get_students(batch_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT student_id, name, roll_no, encoding FROM students WHERE batch_id = ? ORDER BY name",
        (batch_id,),
    ).fetchall()
    conn.close()
    return rows


def delete_student(student_id):
    conn = get_connection()
    conn.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
    conn.commit()
    conn.close()


# --- Attendance --------------------------------------------------------------

def mark_attendance(student_id, batch_id, date_str, status):
    conn = get_connection()
    conn.execute(
        """INSERT INTO attendance (student_id, batch_id, date, status, time)
           VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(student_id, date) DO UPDATE SET status = excluded.status, time = excluded.time""",
        (student_id, batch_id, date_str, status, datetime.now().strftime("%H:%M:%S")),
    )
    conn.commit()
    conn.close()


def get_attendance_by_date(batch_id, date_str):
    conn = get_connection()
    rows = conn.execute(
        """SELECT s.name, s.roll_no, a.status, a.time FROM attendance a
           JOIN students s ON s.student_id = a.student_id
           WHERE a.batch_id = ? AND a.date = ? ORDER BY s.name""",
        (batch_id, date_str),
    ).fetchall()
    conn.close()
    return rows


def get_attendance_by_student(student_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT date, status, time FROM attendance WHERE student_id = ? ORDER BY date DESC",
        (student_id,),
    ).fetchall()
    conn.close()
    return rows


def get_summary(batch_id):
    conn = get_connection()
    rows = conn.execute(
        """SELECT s.name, s.roll_no,
                  SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) AS present,
                  COUNT(a.status) AS total
           FROM students s LEFT JOIN attendance a ON a.student_id = s.student_id
           WHERE s.batch_id = ? GROUP BY s.student_id ORDER BY s.name""",
        (batch_id,),
    ).fetchall()
    conn.close()
    return rows
