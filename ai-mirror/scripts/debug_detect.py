import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # add project root to PYTHONPATH
import cv2, time
from utils.vision import detect_faces_fast

# Try DirectShow first (stable on many Windows setups). If it fails, switch to MSMF.
def open_cam(index=0):
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap.release()
        cap = cv2.VideoCapture(index, cv2.CAP_MSMF)
    return cap

for cam_index in (0, 1, 2):
    cap = open_cam(cam_index)
    print(f"[INFO] Trying camera index {cam_index} ... opened={cap.isOpened()}")
    if cap.isOpened():
        break

if not cap or not cap.isOpened():
    raise RuntimeError("No camera opened. Try unplug/replug, different USB port, or close other camera apps.")

cv2.namedWindow("Debug Detect", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Debug Detect", 960, 540)
print("[INFO] Press 'q' to quit.")

while True:
    ok, frame = cap.read()
    if not ok:
        print("[WARN] cap.read() failed; retrying...")
        time.sleep(0.05)
        continue

    boxes = detect_faces_fast(frame, detect_scale=0.9)
    for (t, r, b, l) in boxes:
        cv2.rectangle(frame, (l, t), (r, b), (0, 255, 0), 2)

    cv2.putText(frame, f"faces: {len(boxes)}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

    cv2.imshow("Debug Detect", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
