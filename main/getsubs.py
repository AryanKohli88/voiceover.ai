import os
import speech_recognition as sr
from pydub import AudioSegment
from pydub.silence import split_on_silence

def generate_subtitles(audio_path):
    # Create the 'test1' folder if it doesn't exist
    output_folder = "test1"
    os.makedirs(output_folder, exist_ok=True)

    r = sr.Recognizer()
    audio = AudioSegment.from_wav(audio_path)
    chunks = split_on_silence(audio, min_silence_len=500, silence_thresh=-40)
    
    subtitles = []
    current_speaker = 1
    for i, chunk in enumerate(chunks):
        chunk_path = os.path.join(output_folder, f"temp_chunk_{i}.wav")
        chunk.export(chunk_path, format="wav")
        with sr.AudioFile(chunk_path) as source:
            audio_data = r.record(source)
            try:
                text = r.recognize_google(audio_data)
                start_time = sum(len(c) for c in chunks[:i]) / 1000
                end_time = start_time + len(chunk) / 1000
                subtitles.append((start_time, end_time, f"Speaker {current_speaker}", text))
                current_speaker = 3 - current_speaker  # Alternate between 1 and 2
            except sr.UnknownValueError:
                pass
        
        # Remove the temporary chunk file
        os.remove(chunk_path)
    
    return subtitles

def write_srt(subtitles, output_file):
    # Ensure the output file is in the 'test1' folder
    output_folder = "test1"
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, output_file)

    with open(output_path, 'w', encoding='utf-8') as f:
        for i, (start, end, speaker, text) in enumerate(subtitles, 1):
            f.write(f"{i}\n")
            f.write(f"{format_time(start)} --> {format_time(end)}\n")
            f.write(f"{speaker}: {text}\n\n")

def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}".replace('.', ',')
