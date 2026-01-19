import os
import requests
import time
from google import genai
import time
import json

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


def translate_lines_to_hindi(lines, chat):
    try:
        response = chat.send_message(lines)
        raw = response.text.strip()

        # Split into individual translations
        data = [line.strip() for line in raw.split("\n") if line.strip()]

        # Fix length mismatches
        if len(data) != len(lines):
            print(f"WARNING: expected {len(lines)} lines but got {len(data)}")
            if len(data) > len(lines):
                data = data[:len(lines)]
            else:
                data += [""] * (len(lines) - len(data))

        return data

    except Exception as e:
        print(f"Error: {e}")
        return [""] * len(lines)
    finally:
      print(f"Translation stopped or completed.")


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

def transcribe_file(outputsrtfile, session_id, deep_key, google_key, progress_bar, input_lang, speaker_lang):
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
                'language': speaker_lang,
                'smart_format': 'true',
                'diarize': 'true'
            },
            data=audio
        )

    if response.status_code != 200:
        return f"Deepgram API error: {response.text}"

    result = response.json()
    paragraphs = result['results']['channels'][0]['alternatives'][0]['paragraphs']['paragraphs']
    

    progress_bar.progress(55)

    client = genai.Client(
    api_key=google_key,
    )

    chat = client.chats.create(model="gemini-2.5-flash")
    initial_prompt = (
        "You are a subtitle translation engine. I will give you a LIST (array) of "
        + speaker_lang +
        " subtitle lines.\n\n"

        "Your task:\n"
        "1. Translate EACH item into natural, conversational "
        + input_lang +
        " in the " + input_lang +
        " script.\n"
        "2. Keep tone modern, natural, suitable for dubbing.\n"
        "3. Keep the SAME ORDER — one output item for EACH input item.\n"
        "4. Write numbers in words (e.g., 2020 → 'Two thousand twenty').\n"
        "5. If a word must remain in "
        + speaker_lang +
        ", keep it but written in " + input_lang +
        " script.\n\n"

        "CRITICAL OUTPUT RULES:\n"
        "- ONE TRANSLATED LINE PER OUTPUT LINE.\n"
        "- No explanations.\n"
        "- No extra text.\n"
        "- No numbering.\n"
        "- No markdown.\n"
        "- No brackets.\n"
        "- No blank lines.\n"
        "- No surrounding comments.\n"

        "Example output:\n"
        "Translated line 1\n"
        "Translated line 2\n"
        "Translated line 3\n"

        "If you cannot translate a line, return an empty string for that item and move to next line.\n"
    )

    prompt_for_pokemon = (
    "You are a professional Hindi dubbing scriptwriter. Translate the provided list of English lines "
    "into natural, conversational, and modern Hindi. Follow these strict rules for every output:\n\n"
    "1. Language Independent Words: Transliterate names and English terms into Devanagari using "
    "modern phonetics. Use 'ऐ' (double matra) for the 'a' sound in words like 'man' (e.g., Charmander "
    "as चारमैन्डर), whereas Shonen remains शोनेन. Use the 'ॉ' (Chandra) symbol for the open 'o' sound in words like "
    "'pot' or 'poly' (e.g., Poliwhirl as पॉलीवर्ल). Use standard 'व' for 'w/wh' sounds. Pokeball becomes 'पोकेबॉल' and evolves becomes 'इवॉल्व्ज़'. \n"
    "2. Tone, modern Vocabulary & Grammar: Keep the language modern and suitable for natural voice acting and dubbing. Use modern, conversational Hindi instead of textbook/formal Hindi."
    "For example, always use 'वो' instead of 'वह' for 'he/she/that'. and write 'favourite' as फेवरेट "
    "instead of पसंदीदा.Kangaskhan becomes कैन्‍गसख़ान. Pikachi becomes पिकाचू.\n"
    "3. Numbers: Write all numbers out as words in the language they are spoken (e.g., 2024 as "
    "टू थाउजेंड ट्वेंटी फोर).\n"
    "4. English Words: If a word is better left in English for natural flow, keep it but write it "
    "in Devanagari script.\n"
    "5. Formatting: Provide exactly one output line for each input line. Maintain the original order. "
    "Strictly no numbering, no markdown (no bold/italics), no brackets, no blank lines, and no "
    "explanations. If a line cannot be translated, return an empty string for that line.\n"
    "6. Output only the translated lines.\n\n"
    "Example output:\n"
    "नमस्ते आप कैसे हैं?\n"
    "चारमैन्डर मेरा फेवरेट है\n"
    "पॉलीवर्ल को देखो\n"
    "मैने टू थाउजेंड ट्वेंटी में ये शुरू किया"
)
    
    response = chat.send_message(prompt_for_pokemon)
    print(response.text)

    all_texts = []
    for paragraph in paragraphs:
        for sentence in paragraph['sentences']:
            all_texts.append(sentence['text'])

    translated_texts = translate_lines_to_hindi(all_texts, chat)

    srt_content = ""
    counter = 1
    i=0

    for paragraph in paragraphs:
        for sentence in paragraph['sentences']:
            start = seconds_to_srt_time(sentence['start'])
            end = seconds_to_srt_time(sentence['end'])
            print("writing srt for index:", i)
            translated_text = translated_texts[i]  # get correct translated line
            i += 1

            srt_content += f"{counter}\n{start} --> {end}\n{translated_text}\n\n"
            counter += 1

    with open(outputsrtfile, "w", encoding="utf-8") as srt_file:
        srt_file.write(srt_content)

    return 'Success'
