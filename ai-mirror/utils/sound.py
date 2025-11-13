# utils/sound.py
import os
import io
import time
import contextlib

OPENAI_KEY = os.getenv("OPENAI_API_KEY")

# ---- Offline TTS (Windows SAPI via pyttsx3) ----
_engine = None
def _ensure_pyttsx3():
    global _engine
    if _engine is None:
        import pyttsx3  # lazy import
        _engine = pyttsx3.init(driverName="sapi5")  # force SAPI5 on Windows
        _engine.setProperty("rate", 185)            # tweak to taste
        _engine.setProperty("volume", 1.0)

def say_offline(text: str):
    _ensure_pyttsx3()
    _engine.say(text)
    _engine.runAndWait()

# ---- Online TTS via OpenAI ----
def say_online(text: str):
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_KEY)
    # Use tts-1 (or tts-1-hd) with a common voice
    resp = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text
    )
    # resp is a streaming object; get bytes and play
    audio_bytes = resp.read()
    # Simple playback without extra deps: write a temp WAV and play it via winsound
    import tempfile, winsound
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        f.write(audio_bytes)
        path = f.name
    winsound.PlaySound(path, winsound.SND_FILENAME)

def say(text: str):
    """Speak text, using OpenAI TTS when available, else offline SAPI."""
    print(f"[TTS] {text}")
    try:
        if OPENAI_KEY:
            say_online(text)
        else:
            say_offline(text)
    except Exception as e:
        print(f"[TTS] Fallback -> offline (reason: {e})")
        try:
            say_offline(text)
        except Exception as e2:
            print(f"[TTS] Failed to speak: {e2}")
            # last-resort quiet failure; no beep spam
