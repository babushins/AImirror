# utils/voice.py
import time
import speech_recognition as sr

# Set this to the working mic index (or leave None to use OS default).
PREFERRED_IDX = None  # e.g. 8

def _make_mic(idx=None):
    """Create an sr.Microphone safely for the chosen index."""
    if idx is None:
        return sr.Microphone()
    return sr.Microphone(device_index=idx)

def try_listen(idx=None, culture="en-US", timeout=6.0, phrase_time_limit=6.0):
    """
    One-shot listen; returns recognized text or None.
    Prints friendly diagnostics but never raises.
    """
    r = sr.Recognizer()
    # keep energy threshold reasonable and adapt briefly
    r.dynamic_energy_threshold = True
    r.pause_threshold = 0.6

    try:
        with _make_mic(idx) as source:
            print("[VOICE] Say something! (Speak clearly for ~5 seconds...)")
            try:
                r.adjust_for_ambient_noise(source, duration=0.3)
            except Exception:
                # not fatal; continue
                pass

            audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

        # recognition (Google Speech recognizer; swap if you use another)
        text = r.recognize_google(audio, language=culture)
        print(f"[VOICE] Recognized: {text}")
        return text

    except sr.WaitTimeoutError:
        print("[VOICE] Timeout: nothing heard.")
    except sr.UnknownValueError:
        print("[VOICE] Sorry, I couldn’t understand.")
    except sr.RequestError as e:
        print(f"[VOICE] Recognition service error: {e}")
    except OSError as e:
        # typical when device index is wrong or device is busy
        print(f"[VOICE] Mic error: {e}")
    except Exception as e:
        print(f"[VOICE] Unexpected error: {e}")

    return None
