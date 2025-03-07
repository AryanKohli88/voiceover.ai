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
