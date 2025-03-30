from moviepy import VideoFileClip
import os

def extract_audio(video_path):
    output_folder = "test1"
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, "extracted_audio.wav")
    
    video = VideoFileClip(video_path)
    audio = video.audio
    audio.write_audiofile(output_path)
    video.close()

    return output_path


# TODO:
# Divide audio into chunks spoken by different speakers.
# Combine the cunks with enough space in between so that other speaker's dialog can be inserted.
# Need a way to process audio and realise the speaker has changed
# 1. Alternate implementation -> go through the audio and identify number of speakers and store their identity. 
# 2. Also remove BG music and SFX (that does not constitue as a dialogue). This clearer file will be used for subtitles generation.
# 3. Now for n speakers Go through the audio n times and generate n audio files, one file should have dialogues of only one speaker and others should be muted.
