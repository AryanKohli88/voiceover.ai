import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()
AUDIO_FILE_PATH = "./audio_to_translate/speaker2.wav"
API_KEY = os.getenv("API_KEY")

# Helper function to convert seconds to SRT timestamp format
def seconds_to_srt_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    return f"{hours:02}:{minutes:02}:{secs:02},{ms:03}"

def transcribe_file(outputsrtfile):
    with open(AUDIO_FILE_PATH, 'rb') as audio:
        response = requests.post(
            'https://api.deepgram.com/v1/listen',
            headers={
                'Authorization': f'Token {API_KEY}',
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
        raise Exception(f"Deepgram API error: {response.text}")

    result = response.json()
    paragraphs = result['results']['channels'][0]['alternatives'][0]['paragraphs']['paragraphs']
    
    srt_content = ""
    counter = 1

    for paragraph in paragraphs:
        for sentence in paragraph['sentences']:
            start = seconds_to_srt_time(sentence['start'])
            end = seconds_to_srt_time(sentence['end'])
            text = sentence['text']

            srt_content += f"{counter}\n{start} --> {end}\n{text}\n\n"
            counter += 1

    with open(outputsrtfile, "w", encoding="utf-8") as srt_file:
        srt_file.write(srt_content)

    print("SRT file generated successfully!")

if __name__ == "__main__":
    transcribe_file("subtitles.srt")
