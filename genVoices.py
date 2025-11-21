import os
from pydub import AudioSegment
import re
from datetime import datetime, timedelta
import sys
from gtts import gTTS
import subprocess
import requests
import math

def parse_srt_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    entries = content.strip().split('\n\n')
    parsed_subtitles = []

    time_pattern = re.compile(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})")

    for entry in entries:
        lines = entry.split('\n')
        if len(lines) >= 3:
            time_match = time_pattern.match(lines[1])
            if time_match:
                start_str, end_str = time_match.groups()

                def time_str_to_seconds(t):
                    dt = datetime.strptime(t, '%H:%M:%S,%f')
                    td = timedelta(hours=dt.hour, minutes=dt.minute, seconds=dt.second, microseconds=dt.microsecond)
                    return td.total_seconds()

                start = time_str_to_seconds(start_str)
                end = time_str_to_seconds(end_str)

                text_lines = lines[2:]
                full_text = ' '.join(text_lines)

                speaker_match = re.match(r'(Speaker\d+):\s*(.*)', full_text)
                if speaker_match:
                    speaker = speaker_match.group(1)
                    text = speaker_match.group(2)
                else:
                    speaker = 'Speaker1'
                    text = full_text

                parsed_subtitles.append((start, end, speaker, text))

    return parsed_subtitles

def generate_voice_overs(translated_subtitles, output_file, mini_rate, session_id, input_lang):
    # Create the 'result' folder if it doesn't exist
    output_folder = f"result/{session_id}"
    os.makedirs(output_folder, exist_ok=True)

    combined_audio = AudioSegment.silent(duration=0)

    for idx, (start, end, speaker, text) in enumerate(translated_subtitles):
        word_count = len(text.strip().split())
        wanted_duration_sec = end - start
        if wanted_duration_sec <= 0 or word_count == 0:
            continue

        # Step 1: Generate TTS audio as MP3
        tts = gTTS(text=text, lang=input_lang)  # or 'hi' for Hindi etc.
        temp_mp3_path = os.path.join(output_folder, f'temp_{idx}.mp3')
        temp_sped_path = os.path.join(output_folder, f'temp_{idx}_sped.wav')
        tts.save(temp_mp3_path)
        temp_audio = AudioSegment.from_file(temp_mp3_path)
        actual_duration_ms = len(temp_audio)        # duration in milliseconds
        wanted_duration_sec = wanted_duration_sec*1000
        playback_speed = actual_duration_ms/wanted_duration_sec

        # Step 2: Convert to AudioSegment and adjust speed
        subprocess.run([
            "ffmpeg", "-y", "-i", temp_mp3_path,
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
        os.remove(temp_mp3_path)

    output_path = os.path.join(output_folder, output_file)
    combined_audio.export(output_path, format="wav")

    return output_path

# if len(sys.argv) > 1:
#     try:
#         mini_rate = int(sys.argv[1])
#         print(f"Received mini_rate: {mini_rate} and voice_index: {voice_index}")
#     except ValueError:
#         print("Both mini_rate and voice_index must be integers.")
# else:
#     print("No input provided. Usage: python app.py <mini_rate> <voice_index>")

def genvoices(final_subs, mini_rate, session_id, input_lang, klefki_key, duration):
    
    # Call Klefki POST API
    api_url = "https://klefki-backend-fra.onrender.com/klefki-api"
    payload = {
    "expense_UKK": klefki_key,
    "expense_value": math.ceil(duration/60),
    "tool_ID_byDev": "tool_id_28b5a351-6990-4a15-bdb5-e00cbd605513"
    }

    newsubs_parsed = parse_srt_file(final_subs)
    generate_voice_overs(newsubs_parsed, "HindiAudio.wav", mini_rate, session_id, input_lang)

    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()  # raises exception for HTTP errors
        print("✅ POST API response:", response.json())
    except requests.exceptions.RequestException as e:
        print("❌ Failed to call API:", e)


    print('➡️ Next command to run:')
    print('svc infer result/HindiAudio1.wav -m G_70.pth -c config.json')
    return 'success'