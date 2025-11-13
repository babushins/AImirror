import cv2

BACKENDS = [
    ("CAP_DSHOW", cv2.CAP_DSHOW),
    ("CAP_MSMF",  cv2.CAP_MSMF),
    ("CAP_ANY",   cv2.CAP_ANY),
]

def try_open(idx, backend):
    cap = cv2.VideoCapture(idx, backend)
    ok = cap.isOpened()
    if ok:
        ok2, frame = cap.read()
        h, w = (frame.shape[:2] if ok2 and frame is not None else (0, 0))
        cap.release()
        return True, (w, h)
    return False, (0, 0)

print("OpenCV:", cv2.__version__)
for name, be in BACKENDS:
    print(f"\n=== Backend {name} ===")
    for i in range(0, 6):  # try indices 0..5
        ok, (w, h) = try_open(i, be)
        print(f"  index {i}: opened={ok} size={w}x{h}")

