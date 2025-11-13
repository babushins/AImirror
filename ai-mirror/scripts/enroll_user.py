import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # add project root to PYTHONPATH
import os, cv2, argparse, time
from utils.vision import detect_faces_fast, crop_gray

def open_cam(index: int):
    # Try DirectShow first (often best on Windows), then MSMF
    for name, flag in (("CAP_DSHOW", cv2.CAP_DSHOW), ("CAP_MSMF", cv2.CAP_MSMF), ("CAP_ANY", cv2.CAP_ANY)):
        cap = cv2.VideoCapture(index, flag)
        if cap.isOpened():
            print(f"[INFO] Opened camera {index} with {name}", flush=True)
            return cap
        cap.release()
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--count", type=int, default=30)
    ap.add_argument("--camera", type=int, default=0)
    ap.add_argument("--detect_scale", type=float, default=0.8)
    args = ap.parse_args()

    out_dir = os.path.join("data", "users", args.name)
    os.makedirs(out_dir, exist_ok=True)

    cap = open_cam(args.camera)
    if cap is None:
        raise RuntimeError(f"Could not open camera index {args.camera}. Try another index (0/1/2) or close other apps using the camera.")

    saved = 0
    print(f"[INFO] Enrolling '{args.name}'. Move your head, vary angle/distance. Press 'q' to quit.")
    try:
        while saved < args.count:
            ok, frame = cap.read()
            if not ok:
                print("[WARN] cap.read() failed; retrying...", flush=True)
                time.sleep(0.05)
                continue

            boxes = detect_faces_fast(frame, detect_scale=args.detect_scale)
            if not boxes:
                cv2.imshow("Enroll", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'): break
                continue

            # largest face
            boxes.sort(key=lambda b: (b[2]-b[0])*(b[1]-b[3]), reverse=True)
            face = crop_gray(frame, boxes[0])
            if face is None:
                continue

            path = os.path.join(out_dir, f"img_{saved:03d}.jpg")
            cv2.imwrite(path, face)
            saved += 1
            print(f"Saved {saved}/{args.count}: {path}", flush=True)

            cv2.imshow("Enroll", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'): break

    finally:
        cap.release()
        cv2.destroyAllWindows()

    print(f"[DONE] Enrolled {args.name} with {saved} images at {out_dir}")

if __name__ == "__main__":
    main()
