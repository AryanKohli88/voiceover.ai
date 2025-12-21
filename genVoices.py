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
    
    print(f"DEBUG: File content length: {len(content)} chars")
    print(f"DEBUG: First 200 chars:\n{repr(content[:200])}")

    parsed_subtitles = []
    time_pattern = re.compile(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})")
    
    # Split by lines and process
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    
    i = 0
    while i < len(lines):
        # Look for a timestamp line
        time_match = time_pattern.match(lines[i])
        if time_match:
            start_str, end_str = time_match.groups()
            
            def time_str_to_seconds(t):
                dt = datetime.strptime(t, '%H:%M:%S,%f')
                td = timedelta(hours=dt.hour, minutes=dt.minute, seconds=dt.second, microseconds=dt.microsecond)
                return td.total_seconds()

            start = time_str_to_seconds(start_str)
            end = time_str_to_seconds(end_str)
            
            # Collect text lines after timestamp (until we hit a digit or end)
            text_lines = []
            i += 1
            while i < len(lines) and not lines[i][0].isdigit():
                text_lines.append(lines[i])
                i += 1
            
            full_text = ' '.join(text_lines)
            
            speaker_match = re.match(r'(Speaker\d+):\s*(.*)', full_text)
            if speaker_match:
                speaker = speaker_match.group(1)
                text = speaker_match.group(2)
            else:
                speaker = 'Speaker1'
                text = full_text
            
            if text.strip():  # Only add if text is not empty
                parsed_subtitles.append((start, end, speaker, text))
        else:
            i += 1

    return parsed_subtitles

def generate_voice_overs(translated_subtitles, output_file, session_id, input_lang, OK_key, OK_endpoint, gold_user, OK_model_name, female_voice, gen_voice_failed):
    # Create the 'result' folder if it doesn't exist
    gen_voice_failed = False
    output_folder = f"result/{session_id}"
    os.makedirs(output_folder, exist_ok=True)
    lang_code = get_lang_code(input_lang)
    if lang_code is None:
        raise ValueError(f"Unsupported language: {input_lang}")

    print(f"DEBUG: translated_subtitles count = {len(translated_subtitles)}")
    if len(translated_subtitles) == 0:
        print("DEBUG: No subtitles found to process!")
        return "", True

    combined_audio = AudioSegment.silent(duration=0)

    for idx, (start, end, speaker, text) in enumerate(translated_subtitles):
        text = text.strip()
        word_count = len(text.split())
        wanted_duration_sec = end - start
        if wanted_duration_sec <= 0 or word_count == 0:
            continue

        print(f"Processing subtitle {idx}: '{text[:50]}...' Duration: {wanted_duration_sec:.2f}s")

        temp_mp3_path = os.path.join(output_folder, f'temp_{idx}.mp3')
        temp_sped_path = os.path.join(output_folder, f'temp_{idx}_sped.wav')
        api_key=OK_key
        endpoint=OK_endpoint
        model_name=OK_model_name
        
        try:
            # Step 1: Generate TTS audio as MP3
            if gold_user:
                voice_gender = 'female' if female_voice else 'male'
                tts = synthesize_voice(
                    api_key=api_key,
                    text=text,
                    output_path=temp_mp3_path,
                    input_language=lang_code,
                    endpoint_url=endpoint,
                    model_name=model_name,
                    input_speaker=voice_gender
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
    combined_audio_length_ms = len(combined_audio)
    print(f"Generated audio length: {combined_audio_length_ms}ms ({combined_audio_length_ms/1000:.2f}s)")
    if combined_audio_length_ms < 500:
        gen_voice_failed = True
        print("Generated audio is too short, marking generation as failed.")
    return output_path, gen_voice_failed

def genvoices(final_subs, session_id, input_lang, klefki_key, duration, OK_key, OK_endpoint, gold_user, OK_model_name, female_voice):
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
    print(f"DEBUG: Parsed {len(newsubs_parsed)} subtitles from {final_subs}")
    for i, (start, end, speaker, text) in enumerate(newsubs_parsed):
        print(f"  Subtitle {i}: {start:.2f}s - {end:.2f}s | {speaker} | {text[:50]}")
    
    gen_voice_failed = False
    klefki_key_failed = False

    output_path, gen_voice_failed = generate_voice_overs(newsubs_parsed, "HindiAudio.wav", session_id, input_lang, OK_key, OK_endpoint, gold_user, OK_model_name, female_voice, gen_voice_failed)

    # try:
    #     response = requests.post(api_url, json=payload)
    #     response.raise_for_status()  # raises exception for HTTP errors
    #     if response.status_code == 200:
    #         print("✅ Klefki POST API call successful.")
    #         klefki_key_failed = False
    #     else:
    #         print(f"❌ Klefki POST API call failed with: {response.json()}")
    #         klefki_key_failed = True
    # except requests.exceptions.RequestException as e:
    #     print("❌ Failed to call API:", e)


    print('➡️ Next command to run:')
    print('svc infer result/HindiAudio1.wav -m G_70.pth -c config.json')
    if klefki_key_failed:
        return "Klefki Key validation failed."
    if gen_voice_failed:
        return "Voice generation failed."
    if not os.path.exists(output_path):
        return "Voice generation failed - output file not found."
    return 'success'
# genvoices('./hackathon.srt', 'testsession', 'english', 'your_klefki_key', 120, 'lIHnQ9WoJrxGtxYXzQ1ZXWXAk', 'https://cloud.olakrutrim.com/v1/audio/generations/krutrim-vachak-1', True, 'krutrim-vachak-1', False)