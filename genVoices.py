import os
from pydub import AudioSegment
import re
from datetime import datetime, timedelta
import sys
from gtts import gTTS
import subprocess
import requests
import math
from synthesize_voice import synthesize_voice
import time

def get_lang_code(lang_name: str) -> str:
    lang_map = {
        "hindi": "hi",
        "bengali": "bn",
        "tamil": "ta",
        "telugu": "te",
        "malayalam": "ml",
        "kannada": "kn",
        "gujarati": "gu",
        "marathi": "mr",
        "punjabi": "pa",
        "urdu": "ur",
        "nepali": "ne",
        "sinhala": "si",
        "english": "en",
        "french": "fr",
        "mandarin (china mainland)": "zh-CN",
        "mandarin (taiwan)": "zh-TW",
        "portuguese": "pt",
        "spanish": "es"
    }

    # normalize input (lowercase, strip spaces)
    lang_name = lang_name.strip().lower()

    return lang_map.get(lang_name, None)   # returns None if not found


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

def generate_voice_overs(translated_subtitles, output_file, session_id, input_lang, OK_key, OK_endpoint, gold_user, OK_model_name):
    # Create the 'result' folder if it doesn't exist
    output_folder = f"result/{session_id}"
    os.makedirs(output_folder, exist_ok=True)
    lang_code = get_lang_code(input_lang)
    if lang_code is None:
        raise ValueError(f"Unsupported language: {input_lang}")

    combined_audio = AudioSegment.silent(duration=0)

    for idx, (start, end, speaker, text) in enumerate(translated_subtitles):
        text = text.strip()
        word_count = len(text.split())
        wanted_duration_sec = end - start
        if wanted_duration_sec <= 0 or word_count == 0:
            continue

        temp_mp3_path = os.path.join(output_folder, f'temp_{idx}.mp3')
        temp_sped_path = os.path.join(output_folder, f'temp_{idx}_sped.wav')
        api_key=OK_key
        endpoint=OK_endpoint
        model_name=OK_model_name
        
        
        try:
            # Step 1: Generate TTS audio as MP3
            if gold_user:
                tts = synthesize_voice(
                    api_key=api_key,
                    text=text,
                    output_path=temp_mp3_path,
                    input_language=lang_code,
                    endpoint_url=endpoint,
                    model_name=model_name
                )
                time.sleep(5) # brief pause to avoid overwhelming the API
            else:
                tts = gTTS(text=text, lang=lang_code)
                tts.save(temp_mp3_path)

            if not os.path.exists(temp_mp3_path) or os.path.getsize(temp_mp3_path) < 500:
                print(f"Skipping index {idx}: MP3 not created or too small")
                continue

            temp_audio = AudioSegment.from_file(temp_mp3_path)
            actual_duration_ms = len(temp_audio)        # duration in milliseconds

            # If audio is too short, skip it
            if actual_duration_ms < 200:
                print(f"Skipping index {idx}: Audio too short")
                continue

            wanted_duration_sec = wanted_duration_sec*1000
            # Avoid divide by zero
            if wanted_duration_sec <= 0:
                continue

            playback_speed = actual_duration_ms/wanted_duration_sec

            # Step 2: Convert to AudioSegment and adjust speed
            subprocess.run([
                "ffmpeg", "-y", "-i", temp_mp3_path,
                "-filter:a", f"atempo={playback_speed}",
                temp_sped_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"Generated audio for index {idx} with playback speed {playback_speed:.2f}")
            voice_over = AudioSegment.from_file(temp_sped_path, format="wav")
            # Step 3: Insert silence padding if needed
            silence_duration = start * 1000 - len(combined_audio)
            if silence_duration > 0:
                combined_audio += AudioSegment.silent(duration=silence_duration)

            combined_audio += voice_over

        except Exception as e:
            print(f"Skipping index {idx} due to error: {e}")
            continue

        finally:
            if os.path.exists(temp_sped_path):
                os.remove(temp_sped_path)
            if os.path.exists(temp_mp3_path):
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

def genvoices(final_subs, session_id, input_lang, klefki_key, duration, OK_key, OK_endpoint, gold_user, OK_model_name):
    # Call Klefki POST API
    cost = math.ceil(duration/60)
    if gold_user:
        cost = cost * 5  # premium users pay 5 times the credits
    api_url = "https://klefki-backend-fra.onrender.com/klefki-api"
    payload = {
    "expense_UKK": klefki_key,
    "expense_value": cost,
    "tool_ID_byDev": "tool_id_28b5a351-6990-4a15-bdb5-e00cbd605513"
    }

    newsubs_parsed = parse_srt_file(final_subs)
    generate_voice_overs(newsubs_parsed, "HindiAudio.wav", session_id, input_lang, OK_key, OK_endpoint, gold_user, OK_model_name)

    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()  # raises exception for HTTP errors
        print("✅ POST API response:", response.json())
    except requests.exceptions.RequestException as e:
        print("❌ Failed to call API:", e)


    print('➡️ Next command to run:')
    print('svc infer result/HindiAudio1.wav -m G_70.pth -c config.json')
    return 'success'