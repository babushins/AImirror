import cv2, sys, time

print("OpenCV:", cv2.__version__, "imshow?", hasattr(cv2, "imshow"), flush=True)

BACKENDS = [
    ("CAP_DSHOW", cv2.CAP_DSHOW),
    ("CAP_MSMF",  cv2.CAP_MSMF),
    ("CAP_ANY",   cv2.CAP_ANY),
]

def try_one(idx, be_name, be_flag):
    print(f"  -> trying index {idx} on {be_name} ...", end="", flush=True)
    cap = cv2.VideoCapture(idx, be_flag)
    ok = cap.isOpened()
    print(" opened=", ok, flush=True)
    if ok:
        ok2, frame = cap.read()
        print("     first read=", ok2, "shape=", (None if not ok2 or frame is None else frame.shape), flush=True)
        cap.release()
    else:
        cap.release()

print("\n=== PROBING CAMERAS ===", flush=True)
for be_name, be_flag in BACKENDS:
    print(f"\nBackend: {be_name}", flush=True)
    for i in range(0, 6):
        try_one(i, be_name, be_flag)

print("\nDone probing.", flush=True)
