from pyannote.audio import Pipeline
from pydub import AudioSegment
import os
from dotenv import load_dotenv
load_dotenv()
# 1. Initialize diarization pipeline
# hf_token=os.getenv("HF_TOKEN")
pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    use_auth_token=os.getenv("HF_TOKEN")
)

# 2. Process audio file
audio_file = "./vocals.wav"
diarization = pipeline(audio_file)

# 3. Load original audio
full_audio = AudioSegment.from_wav(audio_file)

# 4. Create speaker-specific tracks
speaker_tracks = {
    "SPEAKER_00": AudioSegment.silent(duration=len(full_audio)),
    "SPEAKER_01": AudioSegment.silent(duration=len(full_audio))
}

# 5. Populate speaker tracks
for segment, _, speaker in diarization.itertracks(yield_label=True):
    start_ms = int(segment.start * 1000)
    end_ms = int(segment.end * 1000)
    segment_audio = full_audio[start_ms:end_ms]
    
    if speaker in speaker_tracks:
        speaker_tracks[speaker] = speaker_tracks[speaker].overlay(segment_audio, position=start_ms)

# 6. Export results
speaker_tracks["SPEAKER_00"].export("speaker1.wav", format="wav")
speaker_tracks["SPEAKER_01"].export("speaker2.wav", format="wav")
