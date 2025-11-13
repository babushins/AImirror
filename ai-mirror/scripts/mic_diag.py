import pyaudio

pa = pyaudio.PyAudio()

print("\n=== Host APIs ===")
for i in range(pa.get_host_api_count()):
    api = pa.get_host_api_info_by_index(i)
    print(f"[{i}] {api['name']} (devices: {api['deviceCount']})")

print("\n=== Devices ===")
for i in range(pa.get_device_count()):
    d = pa.get_device_info_by_index(i)
    print(f"[{i:2d}] {d['name']:<40} inputs={int(d['maxInputChannels'])} "
          f"rate={int(d.get('defaultSampleRate',0))}")

print("\n=== Try opening default input ===")
try:
    import speech_recognition as sr
    with sr.Microphone() as s:
        print("Default input opened OK")
except Exception as e:
    print("Default input FAILED:", e)

print("\n=== Try opening each input device ===")
for i in range(pa.get_device_count()):
    d = pa.get_device_info_by_index(i)
    if d['maxInputChannels'] > 0:
        try:
            stream = pa.open(format=pyaudio.paInt16, channels=1,
                             rate=int(d.get('defaultSampleRate', 16000)),
                             input=True, input_device_index=i, frames_per_buffer=1024)
            stream.close()
            print(f"[OK ] {i}: {d['name']}")
        except Exception as e:
            print(f"[ERR] {i}: {d['name']} -> {e}")

pa.terminate()
