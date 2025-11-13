import cv2, time

CAM_INDEX = 0  # try 1 or 2 if needed

cap = cv2.VideoCapture(CAM_INDEX)
if not cap.isOpened():
    raise RuntimeError("Camera not available. Try CAM_INDEX=1 or check /dev/video*")

prev = time.time()
frames = 0
fps = 0.0

print("[INFO] Press 'q' to quit.")
while True:
    ok, frame = cap.read()
    if not ok:
        continue

    frames += 1
    now = time.time()
    if now - prev >= 1.0:
        fps = frames / (now - prev)
        frames = 0
        prev = now

    cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
    cv2.imshow("Camera Test", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

