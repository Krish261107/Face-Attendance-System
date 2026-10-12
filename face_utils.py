"""
face_utils.py — face detection, encoding, matching using dlib directly
(same 128-d model as the `face_recognition` package, without its dlib build issues).
"""

import dlib
import numpy as np
import face_recognition_models as models

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(models.pose_predictor_five_point_model_location())
encoder = dlib.face_recognition_model_v1(models.face_recognition_model_location())


def encode_all_faces(image_rgb):
    """Every face in a (possibly group) photo -> list of 128-d encodings."""
    img = np.ascontiguousarray(image_rgb)
    return [np.array(encoder.compute_face_descriptor(img, predictor(img, rect)))
            for rect in detector(img, 1)]


def encode_single_face(image_rgb):
    """For registration: exactly one face expected. Returns (encoding, error)."""
    encodings = encode_all_faces(image_rgb)
    if not encodings:
        return None, "No face detected — retake with better lighting."
    if len(encodings) > 1:
        return None, "More than one face detected — please crop to just one person."
    return encodings[0], None


def match_face(encoding, known_students, tolerance=0.5):
    """Returns the closest student's id if within tolerance, else None."""
    if not known_students:
        return None
    known = np.array([np.frombuffer(s["encoding"], dtype=np.float64) for s in known_students])
    distances = np.linalg.norm(known - encoding, axis=1)
    best = int(np.argmin(distances))
    return known_students[best]["student_id"] if distances[best] <= tolerance else None
