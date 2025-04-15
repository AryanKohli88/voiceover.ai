from pyannote.audio import Pipeline
from pydub import AudioSegment
import os
from huggingface_hub import login

# === CONFIGURATION ===
AUDIO_PATH = "../seperated/htdemucs/outputwav_002/vocals.wav"  # Input mono WAV file
OUTPUT_DIR = "split_speakers"  # Folder to save speaker tracks
MODEL_NAME = "pyannote/speaker-diarization"

# === STEP 1: Load pipeline ===
print("Loading diarization pipeline...")
# pipeline = Pipeline.from_pretrained(MODEL_NAME)
login("token")  # only needed once per session

pipeline = Pipeline.from_pretrained(MODEL_NAME, use_auth_token="token")

# === STEP 2: Run diarization ===
print("Running speaker diarization...")
diarization = pipeline(AUDIO_PATH)

# === STEP 3: Load audio ===
print("Loading original audio...")
audio = AudioSegment.from_wav(AUDIO_PATH)

# === STEP 4: Create output folder ===
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === STEP 5: Split and save per speaker ===
speaker_segments = {}

for turn, _, speaker in diarization.itertracks(yield_label=True):
    start_ms = int(turn.start * 1000)
    end_ms = int(turn.end * 1000)

    segment = audio[start_ms:end_ms]
    
    if speaker not in speaker_segments:
        speaker_segments[speaker] = segment
    else:
        speaker_segments[speaker] += segment

# === STEP 6: Export audio files ===
print("Saving individual speaker files...")
for speaker, segment in speaker_segments.items():
    output_path = os.path.join(OUTPUT_DIR, f"{speaker}.wav")
    segment.export(output_path, format="wav")
    print(f"Saved: {output_path}")

print("✅ Done!")
