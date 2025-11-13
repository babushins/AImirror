# utils/emotion.py
def estimate_emotion_from_face(face_bgr):
    """
    Return a coarse emotion label ('happy', 'sad', 'angry', 'surprise', 'neutral', ...).
    If the optional FER package isn't installed, we fall back to 'neutral'.
    """
    try:
        import cv2
        from fer import FER  # pip install fer==22.4.0

        if face_bgr is None:
            return "neutral"

        # FER expects RGB
        face_rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
        detector = FER(mtcnn=False)
        emotions = detector.detect_emotions(face_rgb)
        if not emotions:
            return "neutral"

        # Pick the highest scoring emotion
        scores = emotions[0]["emotions"]
        return max(scores, key=scores.get) or "neutral"

    except Exception:
        return "neutral"
