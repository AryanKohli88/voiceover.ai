import os
import pyttsx3
from pydub import AudioSegment
import re
from datetime import datetime, timedelta
import sys
# import asyncio
# from googletrans import Translator

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

def generate_voice_overs(translated_subtitles, output_file, mini_rate, voice_index):
    # Create the 'result' folder if it doesn't exist
    output_folder = "result"
    os.makedirs(output_folder, exist_ok=True)

    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('rate', 280) 
    
    combined_audio = AudioSegment.silent(duration=0)
    
    for start, end, speaker, text in translated_subtitles:
        word_count = len(text.strip().split())
        duration_sec = end - start
        # Avoid division by zero
        if duration_sec <= 0 or word_count == 0:
            continue
        rate = int((word_count * 60) / duration_sec)
        rate = max(mini_rate, min(rate, 300)) # minimin rate value here is 180
        # print("rate :: " + str(rate))
        # print("start :: "+ str(start))
        # print("end :: "+ str(end))

        engine.setProperty('rate', rate)
        # engine.setProperty('voice', voices[int(speaker[-1]) - 1].id)
        engine.setProperty('voice', voices[voice_index].id)
        temp_voice_path = os.path.join(output_folder, 'temp_voice.wav')
        engine.save_to_file(text, temp_voice_path)
        engine.runAndWait()
        # print("length till now " + str(len(combined_audio)) )
        voice_over = AudioSegment.from_wav(temp_voice_path)
        trimmed_audio = voice_over[:-int(420)] # triming 420 mili seconds (10 frames for 24 fps) of silence
        silence_duration = start * 1000 - len(combined_audio)
        if silence_duration > 0:
            combined_audio += AudioSegment.silent(duration=silence_duration)
        combined_audio += trimmed_audio
        # print("silence of :: " + str(silence_duration))
        # Remove the temporary voice file
        os.remove(temp_voice_path)
    
    # Save the final output in the result folder
    output_path = os.path.join(output_folder, output_file)
    combined_audio.export(output_path, format="wav")

    return output_path

if len(sys.argv) > 1:
    try:
        mini_rate = int(sys.argv[1])
        voice_index = int(sys.argv[2])
        print(f"Received mini_rate: {mini_rate} and voice_index: {voice_index}")
    except ValueError:
        print("Both mini_rate and voice_index must be integers.")
else:
    print("No input provided. Usage: python app.py <mini_rate> <voice_index>")

newsubs_parsed = parse_srt_file('./newsubs.srt')
generate_voice_overs(newsubs_parsed, "HindiAudio1.wav", mini_rate, voice_index)
print('➡️ Next command to run:')
print('svc infer result/HindiAudio1.wav -m G_70.pth -c config.json')