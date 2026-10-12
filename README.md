# Face Recognition Attendance System

A Streamlit app that takes attendance by recognizing student faces from a
classroom photo, organized by batch (Data Science, Web Development, C/C++,
or any batch you add), with date-wise and student-wise reports, and the
ability to remove students or whole batches.

- **Database:** SQLite (a single local file, `attendance.db` — no server, no setup)
- **Face recognition:** the `face_recognition` library (dlib's 128-d deep
  face embedding model) — a well-established, accurate model
- **UI:** Streamlit, running entirely in your browser
- **No conda, no git required.** Just Python + `pip`.

## 1. Install (one-time)

You need Python 3.9–3.12 installed. Then, in a terminal, **inside this
folder**, run:

```bash
python install_dependencies.py
```

That's the whole install step. Don't use `pip install -r requirements.txt`
directly — see why below.

**Important — about `dlib`:** `face_recognition` normally depends on `dlib`,
which needs CMake and a C++ compiler to build from source (this is the
`Failed to build installable wheels for ... dlib` / `CalledProcessError:
... 'cmake' ...` error some people hit on Windows). `install_dependencies.py`
avoids that entirely by installing **`dlib-bin`** first (a precompiled
`dlib`, no compiler needed), then installing `face_recognition` with
`--no-deps` so it never asks pip to fetch the source `dlib` at all. If both
were simply listed together in `requirements.txt`, pip's resolver would
still try to build the source `dlib` to satisfy `face_recognition`'s own
requirement — which is exactly what a plain `pip install -r
requirements.txt` would do, and why that error happens. The installer
script runs the two steps in the right order instead:

```bash
pip install dlib-bin
pip install --no-deps face_recognition face_recognition_models Click
pip install -r requirements.txt    # streamlit, opencv, numpy, pandas, Pillow
```

This exact sequence was tested from a clean environment during development
and installs cleanly with plain `pip` — no CMake, no Visual Studio Build
Tools, no Anaconda.

If `pip install dlib-bin` ever fails for your specific OS/Python version
(rare), fall back to the standard `pip install dlib face_recognition` — that
one *does* need a C++ compiler (on Windows: "Desktop development with C++"
from Visual Studio Build Tools; on Mac: Xcode command line tools; on Linux:
`build-essential` and `cmake`).

If you have more than one Python installed (the traceback mentions things
like `Python Old`), make sure you run `install_dependencies.py` and
`streamlit run app.py` with the *same* `python`/`py` command each time —
otherwise you'll install packages into one Python and run the app with
another.

## 2. Run

```bash
python -m streamlit run app.py
```

Your browser opens automatically to the app. If it doesn't, open the URL
printed in the terminal (usually `http://localhost:8501`).

## 3. Using it

The sidebar has four sections:

- **Manage** — add a batch (Data Science, Web Development, C/C++ are
  pre-created; add as many more as you like), remove an individual
  student, or delete an entire batch (which also removes its students
  and attendance history).
- **Register Student** — pick a batch, enter a name/roll number, and
  capture one clear, front-facing photo with the webcam. The app extracts
  a face "encoding" (a 128-number fingerprint of the face) and stores
  just that — no photo is kept.
- **Take Attendance** — pick a batch and date, then capture a photo of
  the class (one student, a small group, or the whole room — every face
  in the photo is detected and matched at once). Everyone recognized is
  marked Present for that date, everyone else in the batch is marked
  Absent, so attendance percentages are always accurate.
- **Reports** — *Date-wise*: who was present/absent on a given day.
  *Student-wise*: one student's full history and attendance %.
  *Batch summary*: every student's present-count and % across all
  sessions. All downloadable as CSV.

## How the recognition works (and how to tune it)

Each registered face becomes a 128-dimensional numeric vector. When you take
attendance, every face found in the new photo is converted the same way and
compared, by distance, to all stored vectors for that batch — the closest
one under a threshold is the match.

That threshold lives in `app.py`:

```python
MATCH_TOLERANCE = 0.50
```

- Lower it (e.g. `0.45`) if it's confusing two similar-looking students.
- Raise it slightly (e.g. `0.55`) if it's failing to recognize people it
  should, e.g. due to poor lighting or camera angle.

For best accuracy: register with a sharp, evenly-lit, front-facing photo,
and take attendance photos with reasonable lighting and the face(s) not too
small in frame.

## Project files

```
app.py                   Streamlit UI — Manage / Register / Attendance / Reports
database.py               SQLite schema + CRUD (batches, students, attendance)
face_utils.py             Face detection, encoding, and matching
install_dependencies.py   Run once — installs everything in the right order (see above)
requirements.txt          Python dependencies (excluding dlib/face_recognition — see above)
attendance.db             Created automatically on first run
```

## Notes / limitations

- `st.camera_input` captures a single still photo per click (not a live
  video feed) — this is intentional: it keeps the whole system to a `pip
  install` + `streamlit run`, with no extra native camera/streaming
  dependencies, and it works the same on Windows/Mac/Linux and in the
  browser. Taking a couple of photos to cover a full room takes a few
  seconds.
- Only the face encoding (128 numbers) is stored per student — no photo is
  kept on disk.
- Re-processing attendance for the same batch/date overwrites that day's
  result rather than duplicating it, so retaking the class photo is safe.
- This is a local, single-machine tool (SQLite only). If you later want
  multiple people using it over a network at once, SQLite would need to be
  swapped for a server database (e.g. PostgreSQL) — ask if you want that
  version.
