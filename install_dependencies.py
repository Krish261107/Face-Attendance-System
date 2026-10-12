"""
install_dependencies.py
Run this once:   python install_dependencies.py

Why this script exists instead of a plain `pip install -r requirements.txt`:
`face_recognition` normally depends on the real `dlib` package, which needs
CMake + a C++ compiler to build from source. `dlib-bin` is a precompiled
drop-in replacement that avoids that entirely — but pip doesn't know the two
are interchangeable, so if they're both listed in one requirements.txt, pip
will still try (and fail) to build the source `dlib` to satisfy
face_recognition's own dependency list.

The fix is simple: install dlib-bin first, then install face_recognition
with --no-deps so it never asks pip to fetch the source dlib at all. This
script just runs those steps for you, in the right order, using whichever
Python you're currently running (so it installs into the same place
`streamlit run app.py` will look).
"""

import subprocess
import sys


def run(args):
    print(">", " ".join(args))
    subprocess.check_call(args)


def main():
    py = sys.executable
    pip = [py, "-m", "pip"]

    print("Using Python at:", py)
    print()

    # Step 1: precompiled dlib, no compiler needed.
    run(pip + ["install", "dlib-bin"])

    # Step 2: face_recognition WITHOUT letting it pull the real 'dlib' package.
    run(pip + ["install", "--no-deps", "face_recognition", "face_recognition_models", "Click"])

    # Step 3: everything else, normally.
    run(pip + ["install", "-r", "requirements.txt"])

    print()
    print("All dependencies installed. Run the app with:")
    print(f"    {py} -m streamlit run app.py")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print()
        print("Something failed during installation. See the pip output above for the")
        print("exact error. If step 1 (dlib-bin) fails, your Python version/OS may not")
        print("have a precompiled wheel yet — see the README's fallback instructions.")
        sys.exit(1)
