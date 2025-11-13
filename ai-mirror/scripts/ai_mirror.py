# scripts/ai_mirror.py
# AI Mirror – main controller script
# - Voice loop with simple commands
# - Camera + (optional) face/emotion scan
# - LLM replies via OpenAI if OPENAI_API_KEY is set; otherwise offline tips
# - Defensive imports so the app keeps working even if some pieces are missing

from __future__ import annotations

import os
import time
from collections import deque

# ---------- Optional deps (fail-safe imports) ----------
try:
    import cv2  # type: ignore
except Exception:
    cv2 = None

# --- utils.voice ---
# Expecting either:
#   from utils.voice import try_listen
# or a class VoiceRecognizer with .listen_once()
try:
    from utils.voice import try_listen as _try_listen  # preferred
    HAVE_TRY_LISTEN = True
except Exception:
    HAVE_TRY_LISTEN = False
    _try_listen = None
    try:
        from utils.voice import VoiceRecognizer  # fallback
    except Exception:
        VoiceRecognizer = None  # type: ignore

# --- utils.sound (optional TTS) ---
try:
    from utils.sound import say as _say
except Exception:
    _say = None

# --- utils.vision (optional face detect) ---
try:
    from utils.vision import detect_faces_fast
except Exception:
    detect_faces_fast = None

# --- utils.emotion (optional face -> emotion) ---
try:
    from utils.emotion import estimate_emotion_from_face
except Exception:
    estimate_emotion_from_face = None

# --- utils.ai (optional LLM responder) ---
# We support either a simple helper class AIResponder with .reply(ctx, user_text)
# or we’ll build an inline OpenAI call.
AIResponder = None
try:
    from utils.ai import AIResponder  # type: ignore
except Exception:
    AIResponder = None  # type: ignore

# ---------- Small helpers ----------

def say(text: str) -> None:
    """Speak (if TTS available) and always print as console output."""
    print(f"[TTS] {text}")
    try:
        if _say:
            _say(text)
    except Exception:
        # Never break the app on TTS failure
        pass


def try_listen(timeout: float = 6.0, culture: str = "en-US", phrase_time_limit: float = 6.0):
    """
    Normalized speech capture that works whether project provides
    `utils.voice.try_listen` or only `VoiceRecognizer`.
    Returns: str | None
    """
    # Preferred: project-level function
    if HAVE_TRY_LISTEN and _try_listen:
        try:
            return _try_listen(timeout=timeout, culture=culture, phrase_time_limit=phrase_time_limit)
        except Exception:
            return None

    # Fallback: local recognizer
    if VoiceRecognizer is not None:
        try:
            vr = VoiceRecognizer(culture=culture)
            return vr.listen_once(timeout=timeout, phrase_time_limit=phrase_time_limit)
        except Exception:
            return None

    # Last resort: no voice engine
    print("[VOICE] No voice engine available.")
    return None


def _open_camera() -> "cv2.VideoCapture | None":
    if cv2 is None:
        return None
    try:
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) if hasattr(cv2, "CAP_DSHOW") else cv2.VideoCapture(0)
        if not cap or not cap.isOpened():
            return None
        # modest resolution keeps CPU/GPU low
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
        return cap
    except Exception:
        return None


def _read_frame(cap) -> "tuple | None":
    if cv2 is None or cap is None:
        return None
    ok, frame = cap.read()
    if not ok or frame is None:
        return None
    return frame


def _emotion_from_frame(frame) -> str | None:
    """Return coarse emotion string or None if unavailable."""
    if frame is None or cv2 is None:
        return None
    if detect_faces_fast is None or estimate_emotion_from_face is None:
        return None
    try:
        # detect face(s)
        faces = detect_faces_fast(frame)
        if not faces:
            return None
        # Use the largest face
        x, y, w, h = max(faces, key=lambda r: r[2] * r[3])
        face_bgr = frame[y : y + h, x : x + w]
        emotion = estimate_emotion_from_face(face_bgr)  # returns e.g. 'happy', 'sad', ...
        return emotion
    except Exception:
        return None


def _build_ai():
    """
    Make an AI responder, first trying project-level utils.ai.AIResponder.
    Otherwise use openai directly, only if OPENAI_API_KEY looks present.
    """
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY".lower())
    if AIResponder is not None and api_key:
        try:
            return AIResponder(model="gpt-4o-mini")
        except Exception:
            pass

    # Inline OpenAI fallback:
    if api_key:
        try:
            from openai import OpenAI  # type: ignore
            client = OpenAI(api_key=api_key)

            class InlineResponder:
                def __init__(self, model="gpt-4o-mini"):
                    self.model = model

                def reply(self, ctx: list[str], user_text: str) -> str:
                    system_text = (
                        "You are the voice of a smart mirror. Keep replies short, friendly, and helpful."
                    )
                    messages = [{"role": "system", "content": system_text}]
                    for u in ctx[-6:]:  # shallow memory
                        messages.append({"role": "user", "content": u})
                    messages.append({"role": "user", "content": user_text})
                    resp = client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=0.6,
                        max_tokens=120,
                    )
                    return (resp.choices[0].message.content or "").strip()

            return InlineResponder()
        except Exception:
            pass

    # No online AI available
    return None


def _offline_answer(user: str, mood: str | None) -> str:
    """Tiny offline brain so the app remains useful."""
    u = (user or "").lower().strip()
    if not u:
        return "I didn't catch that. Try again?"
    if any(k in u for k in ["weather", "temperature"]):
        return "I can't check live weather yet, but it looks like a good day to drink water and stretch."
    if "time" in u:
        return f"It's {time.strftime('%H:%M')}."
    if "name" in u:
        return "I'm your AI mirror."
    if "camera" in u:
        return "The camera is on for face detection; say 'quit' to exit."
    if mood:
        return f"You look a bit {mood} to me. How can I help?"
    return "Okay."


# ---------- The App ----------

class AIMirror:
    def __init__(self):
        self.model_name = "gpt-4o-mini"
        self.ctx: deque[str] = deque(maxlen=12)
        self.cap = _open_camera()
        self.ai = _build_ai()
        self.muted = False
        self.moods = deque(maxlen=12)

    # --------- basic voice I/O ----------
    def _listen(self) -> str | None:
        text = try_listen(timeout=6.0, culture="en-US", phrase_time_limit=6.0)
        if text:
            print(f"[VOICE] Recognized: {text}")
        else:
            print("[VOICE] Timeout: nothing heard.")
        return text

    def _speak(self, text: str) -> None:
        if not self.muted:
            say(text)
        else:
            print(f"[TTS muted] {text}")

    # --------- main loop ----------
    def run(self):
        # Banner
        key = os.getenv("OPENAI_API_KEY")
        if key and key.startswith(("sk-", "sk-proj", "sk-live", "sk-test", "sk-prod")):
            print(f"[AI] Connected with key prefix: {key[:8]}...")
        else:
            print("[AI] Offline fallback active (set OPENAI_API_KEY to enable LLM).")

        print(f"[AI] Model: {self.model_name}")
        print("[INFO] AI Mirror ready.\n"
              "Voice: say 'mute', 'unmute', 'start timer 25', 'pause timer', "
              "'resume timer', 'status', 'quit'.")

        timer_deadline = None
        paused = False

        while True:
            # ---- camera + emotion (non-blocking) ----
            mood = None
            if self.cap is not None:
                frame = _read_frame(self.cap)
                if frame is not None:
                    mood = _emotion_from_frame(frame)
                    if mood:
                        self.moods.append(mood)
                        print("[MOOD]", mood)

                    # optional preview & quit by 'q'
                    if cv2 is not None:
                        try:
                            cv2.imshow("AI Mirror Camera (press Q to close)", frame)
                            if cv2.waitKey(1) & 0xFF == ord('q'):
                                self._speak("Goodbye.")
                                break
                        except Exception:
                            pass

            # ---- status updates (timer) ----
            if timer_deadline and not paused:
                if time.time() >= timer_deadline:
                    self._speak("Timer done.")
                    timer_deadline = None

            # ---- prompt user ----
            self._speak("Say something! (Speak clearly for ~5 seconds...)")
            user = self._listen()
            if not user:
                continue
            lower = user.lower()

            # ---- commands ----
            if "quit" in lower or "goodbye" in lower:
                self._speak("Goodbye.")
                break

            if "mute" == lower.strip():
                self.muted = True
                print("[VOICE] muted.")
                continue

            if "unmute" == lower.strip():
                self.muted = False
                self._speak("Okay, I can speak again.")
                continue

            if lower.startswith("start timer"):
                # crude minutes/seconds parser: "start timer 25" -> 25 seconds
                try:
                    n = int("".join([c for c in lower if c.isdigit()]) or "25")
                    timer_deadline = time.time() + n
                    paused = False
                    self._speak(f"Timer set for {n} seconds.")
                except Exception:
                    self._speak("Couldn't set the timer.")
                continue

            if "pause timer" in lower:
                if timer_deadline:
                    paused = True
                    self._speak("Timer paused.")
                else:
                    self._speak("No running timer.")
                continue

            if "resume timer" in lower:
                if timer_deadline and paused:
                    paused = False
                    self._speak("Timer resumed.")
                else:
                    self._speak("No paused timer.")
                continue

            if "status" in lower:
                if self.moods:
                    last_mood = self.moods[-1]
                    self._speak(f"I think you're {last_mood}.")
                else:
                    self._speak("I'm running fine.")
                continue

            # ---- AI / offline reply ----
            reply = None
            if self.ai is not None:
                try:
                    reply = self.ai.reply(list(self.ctx), user)
                except TypeError:
                    # Some older utils.ai versions used (user_text) only
                    reply = self.ai.reply(user)  # type: ignore
                except Exception:
                    reply = None

            if reply is None:
                reply = _offline_answer(user, mood)

            self.ctx.append(user)
            self.ctx.append(reply)
            self._speak(reply)

        # ---- cleanup ----
        if self.cap is not None and cv2 is not None:
            try:
                self.cap.release()
                cv2.destroyAllWindows()
            except Exception:
                pass


def main():
    app = AIMirror()
    app.run()


if __name__ == "__main__":
    main()
