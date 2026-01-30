import random
import threading
import sounddevice as sd
import numpy as np
import keyboard
from pathlib import Path
from pydub import AudioSegment

# ===== Указываем ffmpeg =====
AudioSegment.converter = r"D:\ffmpeg-8.0.1\bin\ffmpeg.exe"

# ================= НАСТРОЙКИ =================
MUSIC_FOLDER = Path(r"C:\Users\User\Downloads\сюорка")
VIRTUAL_MIC_NAME = "CABLE Input"
VOLUME = 0.9
BLOCK = 1024
# ============================================

stop_flag = False

def find_device(name):
    for i, d in enumerate(sd.query_devices()):
        if name.lower() in d['name'].lower() and d['max_output_channels'] > 0:
            return i
    raise RuntimeError(f"VB-CABLE '{name}' не найден")

def load_random_track():
    files = [f for f in MUSIC_FOLDER.iterdir() if f.suffix.lower() in ('.mp3', '.wav', '.ogg', '.flac')]
    track = random.choice(files)

    audio = AudioSegment.from_file(track)
    audio = audio.set_channels(2).set_frame_rate(44100)

    samples = np.array(audio.get_array_of_samples()).astype(np.float32)
    samples /= np.iinfo(audio.array_type).max
    samples = samples.reshape((-1, 2))
    samples *= VOLUME

    return samples, 44100, track.name

def play():
    global stop_flag
    stop_flag = False

    audio, sr, name = load_random_track()
    print("🎵", name)

    mic = find_device(VIRTUAL_MIC_NAME)

    with sd.OutputStream(samplerate=sr, channels=2) as spk, \
         sd.OutputStream(samplerate=sr, channels=2, device=mic) as mic_stream:

        idx = 0
        while idx < len(audio) and not stop_flag:
            chunk = audio[idx:idx + BLOCK]
            if len(chunk) < BLOCK:
                chunk = np.pad(chunk, ((0, BLOCK - len(chunk)), (0, 0)))

            spk.write(chunk)
            mic_stream.write(chunk)
            idx += BLOCK

def start():
    threading.Thread(target=play, daemon=True).start()

def stop():
    global stop_flag
    stop_flag = True

# ===== БИНДЫ =====
keyboard.add_hotkey("F8", start)
keyboard.add_hotkey("F12", stop)

print("🎧 READY | F8 Play | F12 Stop")
keyboard.wait()
