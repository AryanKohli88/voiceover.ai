import os
import requests
import time
from google import genai
import time


def read_srt_file(file_path):
    lines = []
    with open(file_path, 'r', encoding='utf-8') as file:
        buffer = []
        for line in file:
            line = line.strip()
            if line == "":
                # End of one subtitle block
                if buffer:
                    lines.append(" ".join(buffer))
                    buffer = []
            elif "-->" not in line and not line.isdigit():
                buffer.append(line)
        # In case the file doesn't end with a blank line
        if buffer:
            lines.append(" ".join(buffer))
    return lines


def translate_lines_to_hindi(subtitles, chat, delay=7):
    translated = ''
    try:
      response = chat.send_message(subtitles)
      reply = response.text.strip()
      translated = reply
    except Exception as e:
      print(f"Error on line {subtitles}: {e}")
    finally:
      print(f"Translation stopped or completed.")
    
    time.sleep(delay) # to stay in free limit of gemini API.
    return translated

def write_translated_srt(original_path, translated_lines, output_path="output_translated.srt"):
    with open(original_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    output_lines = []
    translated_index = 0
    buffer = []

    for line in lines:
        stripped = line.strip()

        if stripped == "":
            # End of a subtitle block
            for buf_line in buffer:
                if "-->" in buf_line or buf_line.isdigit():
                    output_lines.append(buf_line + "\n")
                else:
                    # Replace with translated line
                    if translated_index < len(translated_lines):
                        output_lines.append(translated_lines[translated_index] + "\n")
                        translated_index += 1
            output_lines.append("\n")
            buffer = []
        else:
            buffer.append(stripped)

    # In case the last subtitle block doesn't end with a blank line
    if buffer:
        for buf_line in buffer:
            if "-->" in buf_line or buf_line.isdigit():
                output_lines.append(buf_line + "\n")
            else:
                if translated_index < len(translated_lines):
                    output_lines.append(translated_lines[translated_index] + "\n")
                    translated_index += 1

    with open(output_path, 'w', encoding='utf-8') as out_file:
        out_file.writelines(output_lines)

    print(f"Translated SRT written to {output_path}")


# Helper function to convert seconds to SRT timestamp format
def seconds_to_srt_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    return f"{hours:02}:{minutes:02}:{secs:02},{ms:03}"

def transcribe_file(outputsrtfile, session_id, deep_key, google_key, progress_bar, input_lang):
    AUDIO_FILE_PATH = f"./separated/htdemucs/{session_id}/vocals.wav"
    with open(AUDIO_FILE_PATH, 'rb') as audio:
        response = requests.post(
            'https://api.deepgram.com/v1/listen',
            headers={
                'Authorization': f'Token {deep_key}',
                'Content-Type': 'audio/wav'
            },
            params={
                'model': 'nova-3',
                'smart_format': 'true',
                'diarize': 'true'
            },
            data=audio
        )

    if response.status_code != 200:
        return f"Deepgram API error: {response.text}"

    result = response.json()
    paragraphs = result['results']['channels'][0]['alternatives'][0]['paragraphs']['paragraphs']
    
    srt_content = ""
    counter = 1

    progress_bar.progress(55)

    client = genai.Client(
    api_key=google_key,
    )

    chat = client.chats.create(model="gemini-2.0-flash")
    initial_prompt = "You are a professional subtitle translator. Translate each English subtitle line into **natural, conversational modern " + input_lang + "** suitable for dubbing. Keep it short and localized, like it would appear in a " + input_lang + " movie. Avoid overly formal language unless the tone demands it. Reply with **only the translation**, no extra explanation. Choose the best translation and return only that, don't give me options. Write number in text form, for example 2020 as 'Two thousand twenty' in " + input_lang + ". If the context requires the word to stay in english, write the english word in " + input_lang
    response = chat.send_message(initial_prompt)
    print(response.text)

    for paragraph in paragraphs:
        for sentence in paragraph['sentences']:
            start = seconds_to_srt_time(sentence['start'])
            end = seconds_to_srt_time(sentence['end'])
            text = sentence['text']
            translated_text = translate_lines_to_hindi(text, chat)

            srt_content += f"{counter}\n{start} --> {end}\n{translated_text}\n\n"
            counter += 1

    with open(outputsrtfile, "w", encoding="utf-8") as srt_file:
        srt_file.write(srt_content)

    return 'Success'
