# scripts/list_mics.py
import pyaudio

pa = pyaudio.PyAudio()
print("PyAudio OK. Devices:", pa.get_device_count())
for i in range(pa.get_device_count()):
    info = pa.get_device_info_by_index(i)
    print(f"[{i}] {info.get('name')}")
pa.terminate()
