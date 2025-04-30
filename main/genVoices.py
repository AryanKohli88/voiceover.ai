import os
import pyttsx3
from pydub import AudioSegment

def generate_voice_overs(translated_subtitles, output_file):
    # Create the 'test1' folder if it doesn't exist
    output_folder = "test1"
    os.makedirs(output_folder, exist_ok=True)

    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    
    combined_audio = AudioSegment.silent(duration=0)
    
    for start, end, speaker, text in translated_subtitles:
        engine.setProperty('voice', voices[int(speaker[-1]) - 1].id)
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

README.md