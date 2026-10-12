"""
app.py — Face Recognition Attendance System.
Run with: streamlit run app.py
"""

from datetime import date

import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image

import database as db
import face_utils as fu

st.set_page_config(page_title="Face Attendance System", page_icon="🎓", layout="centered")
db.init_db()

TOLERANCE = 0.5  # face-match strictness: lower = stricter


def to_rgb(camera_file):
    return np.array(Image.open(camera_file).convert("RGB"))


st.sidebar.title("🎓 Face Attendance System")
page = st.sidebar.radio("Go to", ["Manage", "Register Student", "Take Attendance", "Reports"])

batches = db.get_batches()
batch_names = [b["batch_name"] for b in batches]
batch_id_of = {b["batch_name"]: b["batch_id"] for b in batches}

# ---------------------------------------------------------------- Manage ---

if page == "Manage":
    st.header("Manage Batches & Students")

    with st.form("add_batch", clear_on_submit=True):
        new_batch = st.text_input("New batch name")
        if st.form_submit_button("Add batch") and new_batch.strip():
            ok, msg = db.add_batch(new_batch)
            if ok:
                st.rerun()
            st.error(msg)

    if not batches:
        st.info("No batches yet — add one above.")
        st.stop()

    selected_batch = st.selectbox("Batch", batch_names)
    batch_id = batch_id_of[selected_batch]
    students = db.get_students(batch_id)

    st.write(f"**{len(students)} student(s)** in {selected_batch}.")
    if students:
        labels = {f"{s['name']} ({s['roll_no']})" if s["roll_no"] else s["name"]: s["student_id"]
                  for s in students}
        to_remove = st.selectbox("Select student to remove", list(labels.keys()))
        if st.button("Remove student"):
            db.delete_student(labels[to_remove])
            st.rerun()

    if st.button(f"Delete entire batch '{selected_batch}'", type="secondary"):
        db.delete_batch(batch_id)
        st.rerun()

# ------------------------------------------------------- Register Student ---

elif page == "Register Student":
    st.header("Register a Student")

    if not batches:
        st.warning("Add a batch first, on the Manage page.")
        st.stop()

    selected_batch = st.selectbox("Batch", batch_names)
    name = st.text_input("Name")
    roll_no = st.text_input("Roll number / ID")
    photo = st.camera_input("Face photo (front-facing, one person)")

    if st.button("Register"):
        if not name.strip():
            st.error("Enter a name.")
        elif photo is None:
            st.error("Take a photo first.")
        else:
            encoding, err = fu.encode_single_face(to_rgb(photo))
            if err:
                st.error(err)
            else:
                _, msg = db.add_student(name, roll_no, batch_id_of[selected_batch], encoding)
                st.success(msg)

# ------------------------------------------------------------ Attendance ---

elif page == "Take Attendance":
    st.header("Take Attendance")

    if not batches:
        st.warning("Add a batch first, on the Manage page.")
        st.stop()

    selected_batch = st.selectbox("Batch", batch_names)
    batch_id = batch_id_of[selected_batch]
    session_date = st.date_input("Date", value=date.today())

    students = db.get_students(batch_id)
    if not students:
        st.warning(f"No students registered in {selected_batch}.")
        st.stop()

    photo = st.camera_input("Photo of the class (one or many faces)")

    if photo is not None and st.button("Mark Attendance"):
        encodings = fu.encode_all_faces(to_rgb(photo))
        if not encodings:
            st.error("No faces detected — try again.")
        else:
            present_ids = {fu.match_face(e, students, TOLERANCE) for e in encodings}
            present_ids.discard(None)
            date_str = session_date.isoformat()
            for s in students:
                status = "Present" if s["student_id"] in present_ids else "Absent"
                db.mark_attendance(s["student_id"], batch_id, date_str, status)

            st.success(f"{len(present_ids)} present, {len(students) - len(present_ids)} absent.")
            st.table(pd.DataFrame(
                [{"Name": s["name"], "Roll No": s["roll_no"],
                  "Status": "Present" if s["student_id"] in present_ids else "Absent"}
                 for s in students]
            ))

# ---------------------------------------------------------------- Reports ---

elif page == "Reports":
    st.header("Attendance Reports")

    if not batches:
        st.info("No batches yet.")
        st.stop()

    report_type = st.radio("Report", ["Date-wise", "Student-wise", "Batch summary"], horizontal=True)
    selected_batch = st.selectbox("Batch", batch_names)
    batch_id = batch_id_of[selected_batch]

    if report_type == "Date-wise":
        report_date = st.date_input("Date", value=date.today())
        rows = db.get_attendance_by_date(batch_id, report_date.isoformat())
        if not rows:
            st.info("No attendance recorded for this date.")
        else:
            df = pd.DataFrame(rows, columns=["Name", "Roll No", "Status", "Time"])
            st.dataframe(df)
            st.download_button("Download CSV", df.to_csv(index=False).encode(), "date_report.csv")

    elif report_type == "Student-wise":
        students = db.get_students(batch_id)
        if not students:
            st.info("No students in this batch.")
        else:
            labels = {f"{s['name']} ({s['roll_no']})" if s["roll_no"] else s["name"]: s["student_id"]
                      for s in students}
            chosen = st.selectbox("Student", list(labels.keys()))
            rows = db.get_attendance_by_student(labels[chosen])
            if not rows:
                st.info("No attendance history yet.")
            else:
                df = pd.DataFrame(rows, columns=["Date", "Status", "Time"])
                st.dataframe(df)
                st.metric("Attendance %", f"{(df['Status'] == 'Present').mean() * 100:.1f}%")

    else:  # Batch summary
        rows = db.get_summary(batch_id)
        if not rows:
            st.info("No students in this batch.")
        else:
            df = pd.DataFrame(rows, columns=["Name", "Roll No", "Present", "Total"])
            df["Attendance %"] = (df["Present"] / df["Total"].replace(0, 1) * 100).round(1)
            st.dataframe(df)
            st.download_button("Download CSV", df.to_csv(index=False).encode(), "batch_summary.csv")
