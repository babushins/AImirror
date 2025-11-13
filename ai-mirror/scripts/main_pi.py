# main_pi.py  — Windows-friendly Jarvis-like assistant

import os, time, queue, io, tempfile
import numpy as np
import cv2

from openai import OpenAI
import simpleaudio as sa

USE_SOUNDDEVICE = False  # set True if PyAudio fails to install
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

try:
    import speech_recognition as sr
    R_HAS = True
except Exception:
    R_HAS = False

if USE_SOUNDDEVICE:
    import sounddevice as sd
    import soundfile as sf

client = OpenAI(api_key=OPENAI_API_KEY)

def say(text: str) -> None:
    print(f"[TTS] {text}")
    if not OPENAI_API_KEY:
        print("[TTS] No OPENAI_API_KEY. Skipping voice output.")
        return
    try:
        # TTS to a WAV in memory, then play with simpleaudio
        resp = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        audio_bytes = resp.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            f.write(audio_bytes)
            tmp = f.name
        wav = sa.WaveObject.from_wave_file(tmp)
        play = wav.play()
        play.wait_done()
        try:
            os.remove(tmp)
        except Exception:
            pass
    except Exception as e:
        print(f"[TTS] Error: {e}")

def listen_once(timeout=5, phrase_time_limit=6, device_index=None):
    """
    Returns transcribed text (lowercased) or None if nothing.
    Uses SpeechRecognition+PyAudio by default.
    If USE_SOUNDDEVICE=True, records raw audio and feeds to recognizer.
    """
    if not R_HAS:
        print("[VOICE] speech_recognition not available.")
        return None

    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True

    try:
        if not USE_SOUNDDEVICE:
            # Standard path (PyAudio)
            mic = sr.Microphone(device_index=device_index)
            with mic as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.6)
                print("[VOICE] Say something! (Speak clearly for ~5 seconds...)")
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        else:
            # sounddevice fallback path
            samplerate = 16000
            channels = 1
            duration = min(phrase_time_limit, 6)
            print("[VOICE] Say something! (Speak clearly for ~5 seconds...)")
            print("[VOICE] Recording...")
            audio_np = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=channels, dtype="int16")
            sd.wait()
            print("[VOICE] Recorded.")
            # Wrap into an AudioFile for SR
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                sf.write(f.name, audio_np, samplerate)
                tmpwav = f.name
            with sr.AudioFile(tmpwav) as source:
                audio = recognizer.record(source)
            try:
                os.remove(tmpwav)
            except Exception:
                pass

        try:
            text = recognizer.recognize_google(audio, language="en-US")
            print(f"[VOICE] Recognized: {text}")
            return text.strip().lower()
        except sr.UnknownValueError:
            print("[VOICE] Timeout: nothing heard.")
            return None
        except Exception as e:
            print(f"[VOICE] Recognition error: {e}")
            return None
    except Exception as e:
        print(f"[VOICE] Mic error: {e}")
        return None

def mood_from_face_bgr(frame_bgr):
    """Very coarse mood by face size; replace with real classifier if needed."""
    try:
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(60, 60))
        if len(faces) == 0:
            return "neutral", faces
        # Just a silly proxy: bigger face -> 'happy'; few small faces -> 'neutral'
        (x, y, w, h) = max(faces, key=lambda r: r[2] * r[3])
        if w * h > 15000:
            return "happy", faces
        return "neutral", faces
    except Exception:
        return "neutral", []

def tip_for_mood(mood: str) -> str:
    if mood == "happy":
        return "You look upbeat. Keep that energy!"
    if mood == "sad":
        return "You look a bit down. Deep breath—I'm with you."
    return "You look a bit neutral to me. How can I help?"

def chat_reply(user_text: str, mood: str) -> str:
    """
    Send the user_text and mood to GPT for a short spoken reply.
    """
    system = (
        "You are a concise voice assistant on a smart mirror. "
        "Reply in one or two sentences, friendly and helpful. "
        f"The user's current mood is: {mood}."
    )
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_text},
            ],
            temperature=0.7,
            max_tokens=90,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"[AI] Error: {e}")
        return "Sorry, I had trouble thinking just now."

def main():
    if not OPENAI_API_KEY:
        print("[WARN] OPENAI_API_KEY is not set. I'll still listen, but won't speak AI answers.")
    cap = cv2.VideoCapture(0)  # default camera
    if not cap.isOpened():
        print("[CAM] No camera found. Running voice-only mode.")
        cap = None

    print("[INFO] Jarvis mirror ready. Say 'quit' to exit.")
    if cap: say("Hello. Camera is active.")

    while True:
        frame = None
        if cap:
            ok, frame = cap.read()
            if not ok:
                frame = None

        if frame is not None:
            mood, faces = mood_from_face_bgr(frame)
            # draw
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, f"mood: {mood}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255,255,255), 2)
            cv2.imshow("Jarvis Mirror (press Q to quit)", frame)
            if cv2.waitKey(1) & 0xFF in (ord('q'), ord('Q')):
                print("[INFO] Quitting…")
                break
        else:
            mood = "neutral"

        # mood tip (spoken only when camera is on and something was seen recently)
        if cap:
            print(f"[MOOD] {mood}")
            say(tip_for_mood(mood))

        # listen & answer
        user = listen_once()
        if user:
            if user in ("quit", "exit", "goodbye", "good bye"):
                say("Goodbye.")
                break
            reply = chat_reply(user, mood)
            print(f"[AI] {reply}")
            say(reply)

    if cap:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
