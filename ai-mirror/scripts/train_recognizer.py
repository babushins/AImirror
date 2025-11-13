import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # add project root to PYTHONPATH
import os, json, cv2
import numpy as np

DATA = "data/users"
MODELS = "models"
os.makedirs(MODELS, exist_ok=True)

def load_data():
    X, y, labels = [], [], {}
    next_id = 0
    for person in sorted(os.listdir(DATA)):
        pdir = os.path.join(DATA, person)
        if not os.path.isdir(pdir): continue
        if person not in labels:
            labels[person] = next_id; next_id += 1
        for fn in os.listdir(pdir):
            if not fn.lower().endswith((".jpg",".jpeg",".png")): continue
            img = cv2.imread(os.path.join(pdir, fn), cv2.IMREAD_GRAYSCALE)
            if img is None: continue
            X.append(img)
            y.append(labels[person])
    return X, np.array(y, dtype=np.int32), labels

def main():
    X, y, labels = load_data()
    if len(X) == 0:
        raise RuntimeError("No training images. Enroll users first.")
    recognizer = cv2.face.LBPHFaceRecognizer_create(radius=2, neighbors=12, grid_x=8, grid_y=8)
    recognizer.train(X, y)
    recognizer.save(os.path.join(MODELS, "lbph_model.yml"))
    with open(os.path.join(MODELS, "labels.json"), "w", encoding="utf-8") as f:
        json.dump(labels, f)
    print(f"[DONE] Trained on {len(X)} images, {len(set(y))} users.")

if __name__ == "__main__":
    main()
