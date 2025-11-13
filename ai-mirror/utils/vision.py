# utils/vision.py
import cv2

# Use built-in frontal face cascade
_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
_CASCADE = cv2.CascadeClassifier(_CASCADE_PATH)

def detect_faces_fast(frame_bgr):
    """
    Return a list of (x, y, w, h) for faces in a BGR frame.
    Works fast enough for a mirror. Returns [] if none.
    """
    if frame_bgr is None:
        return []
    try:
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        # Slightly larger minSize reduces false positives
        faces = _CASCADE.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(80, 80),
            flags=cv2.CASCADE_SCALE_IMAGE,
        )
        return [(int(x), int(y), int(w), int(h)) for (x, y, w, h) in faces]
    except Exception:
        return []
