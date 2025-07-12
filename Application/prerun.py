import os
import subprocess
import sys
import shutil
import torch
import pyttsx3

engine = pyttsx3.init()
voices = engine.getProperty('voices')
session_id = os.environ.get("SESSION_ID")
video_dir = os.path.join("video", session_id)
# result_dir = os.path.join("result", session_id)
# stems_dir = os.path.join("separated", "htdemucs", session_id)

# input_audio = os.path.join(video_dir, "audio.wav")
# output_audio = os.path.join(result_dir, "HindiAudio1.wav")


# what if already existing audio file is not audio.wav?
# option to add speed of voices
# select index of voice from installed voices
# try with voice index 0, 1 and null

def check_gpu():
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    user_input = input("Do you want to continue? (yes/no): ").strip().lower()
    if user_input != 'yes':
        print("Exiting the program.")
        sys.exit()


# video_folder = "video"
video_extensions = ['.mp4', '.mkv', '.mov', '.avi', '.webm']
audio_extensions = ['.mp3', '.aac', '.ogg', '.flac', '.wav']

def get_file_extension(filename):
    return os.path.splitext(filename)[1].lower()

def is_video_file(filename):
    return get_file_extension(filename) in video_extensions

def is_audio_file(filename):
    return get_file_extension(filename) in audio_extensions

def run_command(command, check=True):
    print(f"Running command: {command}")
    subprocess.run(command, shell=True, check=check)

def convert_video_to_audio(video_path, audio_path):
    print(f"Converting video {video_path} to audio {audio_path}")
    command = f'ffmpeg -i "{video_path}" -vn -acodec pcm_s16le -ar 44100 -ac 2 "{audio_path}" -y'
    run_command(command)

def check_and_install_demucs():
    try:
        subprocess.run(["demucs", "--help"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✅ Demucs is already installed.")
    except FileNotFoundError:
        print("❌ Demucs not found. Installing...")
        run_command("pip install demucs")

# -------------------------------
# Main Logic
# -------------------------------
def is_valid_integer(value):
    return value.isdigit() and int(value) > 0

def main():
    min_rate = 180
    voice_index = 2
    if len(sys.argv) >= 3 and is_valid_integer(sys.argv[1]) and is_valid_integer(sys.argv[2]):
        min_rate = sys.argv[1]
        voice_index = sys.argv[2]
    else:
        print("Usage: invalid values for <min_rate> and <voice_index>")
        return
    
    print(f"Using values {min_rate} and {voice_index}")

    target_audio_path = os.path.join(video_dir, f"{session_id}.wav")
    print("Using Demucs")
    # Step 2: Ensure demucs is installed
    check_and_install_demucs()

    # Step 3: Run demucs
    run_command(f'demucs "{target_audio_path}"')
    print("Demucsing completed")

    # Step 4: Run generateSubs.py
    print("calling generate subs")
    run_command("python generateSubs.py")
    print("completed generate subs")
  
    run_command(f'python genVoices.py {min_rate} {voice_index}')

if __name__ == "__main__":
    main()


