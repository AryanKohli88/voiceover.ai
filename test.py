import os
import os
from pydub import AudioSegment
import re
from datetime import datetime, timedelta
import sys
from gtts import gTTS
import subprocess




def test_generate_voice_overs(translated_subtitles, output_file, mini_rate, session_id):
    # Create the 'result' folder if it doesn't exist
    output_folder = f"result/{session_id}"
    os.makedirs(output_folder, exist_ok=True)

    combined_audio = AudioSegment.silent(duration=0)

    for idx, (start, end, speaker, text) in enumerate(translated_subtitles):
        word_count = len(text.strip().split())
        duration_sec = end - start
        if duration_sec <= 0 or word_count == 0:
            continue

        rate = int((word_count * 60) / duration_sec)
        rate = max(mini_rate, min(rate, 300))  # constrain between mini_rate and 300

        # Estimate playback_speed factor (mini_rate is baseline)
        playback_speed = rate / mini_rate

        # Step 1: Generate TTS audio as MP3
        tts = gTTS(text=text, lang='en')  # or 'hi' for Hindi etc.
        temp_wav_path = os.path.join(output_folder, f'temp_{idx}.wav')
        temp_sped_path = os.path.join(output_folder, f'temp_{idx}_sped.wav')
        tts.save(temp_wav_path)

        # Step 2: Convert to AudioSegment and adjust speed
        if playback_speed < 0.5:
            playback_speed = 0.5
        elif playback_speed > 2.0:
            playback_speed = 2.0

        subprocess.run([
            "ffmpeg", "-y", "-i", temp_wav_path,
            "-filter:a", f"atempo={playback_speed}",
            temp_sped_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        voice_over = AudioSegment.from_file(temp_sped_path)

        # Step 3: Insert silence padding if needed
        silence_duration = start * 1000 - len(combined_audio)
        if silence_duration > 0:
            combined_audio += AudioSegment.silent(duration=silence_duration)
        
        combined_audio += voice_over
        os.remove(temp_sped_path)
        os.remove(temp_wav_path)

    output_path = os.path.join(output_folder, output_file)
    combined_audio.export(output_path, format="wav")

    return output_path
