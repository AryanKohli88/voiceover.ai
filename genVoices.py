import os
from pydub import AudioSegment
import re
from datetime import datetime, timedelta
import sys
from gtts import gTTS
import subprocess


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
        duration_sec = end - start
        if duration_sec <= 0 or word_count == 0:
            continue

        rate = int((word_count * 60) / duration_sec)
        rate = max(mini_rate, min(rate, 300))  # constrain between mini_rate and 300

        # Estimate playback_speed factor (mini_rate is baseline)
        playback_speed = rate / mini_rate

        # Step 1: Generate TTS audio as MP3
        tts = gTTS(text=text, lang=input_lang)  # or 'hi' for Hindi etc.
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

# if len(sys.argv) > 1:
#     try:
#         mini_rate = int(sys.argv[1])
#         print(f"Received mini_rate: {mini_rate} and voice_index: {voice_index}")
#     except ValueError:
#         print("Both mini_rate and voice_index must be integers.")
# else:
#     print("No input provided. Usage: python app.py <mini_rate> <voice_index>")

def genvoices(final_subs, mini_rate, session_id, input_lang):
    newsubs_parsed = parse_srt_file(final_subs)
    generate_voice_overs(newsubs_parsed, "HindiAudio.wav", mini_rate, session_id, input_lang)
    print('➡️ Next command to run:')
    print('svc infer result/HindiAudio1.wav -m G_70.pth -c config.json')
    return 'success'