import os
import pyttsx3
from pydub import AudioSegment
import re
from datetime import datetime, timedelta
import asyncio
from googletrans import Translator

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

def generate_voice_overs(translated_subtitles, output_file):
    # Create the 'result' folder if it doesn't exist
    output_folder = "result"
    os.makedirs(output_folder, exist_ok=True)

    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    
    combined_audio = AudioSegment.silent(duration=0)
    
    for start, end, speaker, text in translated_subtitles:
        # engine.setProperty('voice', voices[int(speaker[-1]) - 1].id)
        engine.setProperty('voice', voices[2].id)
        temp_voice_path = os.path.join(output_folder, 'temp_voice.wav')
        engine.save_to_file(text, temp_voice_path)
        engine.runAndWait()
        
        voice_over = AudioSegment.from_wav(temp_voice_path)
        silence_duration = start * 1000 - len(combined_audio)
        if silence_duration > 0:
            combined_audio += AudioSegment.silent(duration=silence_duration)
        combined_audio += voice_over
        
        # Remove the temporary voice file
        os.remove(temp_voice_path)
    
    # Save the final output in the result folder
    output_path = os.path.join(output_folder, output_file)
    combined_audio.export(output_path, format="wav")

    return output_path

newsubs_parsed = parse_srt_file('./result/translated_subtitles.srt')
generate_voice_overs(newsubs_parsed, "voice.wav")