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


async def translate_text(translator, text, target_language):
    translation = await translator.translate(text, dest=target_language)
    return translation.text

async def translate_subtitle(translator, subtitle, target_language):
    start, end, speaker, text = subtitle
    translated_text = await translate_text(translator, text, target_language)
    return (start, end, speaker, translated_text)

async def translate_subtitles(subtitles, target_language):
    translator = Translator()
    tasks = [translate_subtitle(translator, subtitle, target_language) for subtitle in subtitles]
    translated_subtitles = await asyncio.gather(*tasks)
    return translated_subtitles

def translate_subtitles_sync(subtitles, target_language):
    return asyncio.run(translate_subtitles(subtitles, target_language))

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


def generate_voice_overs(translated_subtitles, output_file):
    # Create the 'test1' folder if it doesn't exist
    output_folder = "test1"
    os.makedirs(output_folder, exist_ok=True)

    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    
    combined_audio = AudioSegment.silent(duration=0)
    
    for start, end, speaker, text in translated_subtitles:
        # engine.setProperty('voice', voices[int(speaker[-1]) - 1].id)
        engine.setProperty('voice', voices[3].id)
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
    
    # Save the final output in the test1 folder
    output_path = os.path.join(output_folder, output_file)
    combined_audio.export(output_path, format="wav")

    return output_path


parsed_subtitles = parse_srt_file('./speaker2.srt')
newsubs = translate_subtitles_sync(parsed_subtitles, "hi")
write_srt(newsubs, "translated_subtitles.srt")

newsubs_parsed = parse_srt_file('./test1/translated_subtitles.srt')
generate_voice_overs(newsubs_parsed, "voice.wav")