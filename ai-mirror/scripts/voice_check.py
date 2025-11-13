# scripts/voice_check.py
import time
from utils.sound import speak
from utils.voice import VoiceRecognizer

CULTURE = "en-US"   # you also have en-GB if you prefer

def main():
    print("[TEST] TTS → saying a line now…")
    speak("Voice test successful. Hello Edgars!", culture=CULTURE)

    print("[TEST] STT → I'll listen for ~10 seconds. Say something like 'mirror status' or 'quit'.")
    rec = VoiceRecognizer(culture=CULTURE)

    heard_anything = False
    try:
        deadline = time.time() + 10
        while time.time() < deadline:
            msg = rec.get(timeout=0.5)  # non-blocking poll
            if msg:
                heard_anything = True
                print(f"[HEARD] {msg}")
                if "quit" in msg.lower():
                    break
        if not heard_anything:
            print("[TEST] No voice captured in 10s. Check mic privacy/input device and try again.")
    finally:
        rec.stop()
        print("[TEST] Done.")

if __name__ == "__main__":
    main()
