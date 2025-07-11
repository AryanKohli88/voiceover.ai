import os
import subprocess
import sys
import shutil
import torch
import pyttsx3

engine = pyttsx3.init()
voices = engine.getProperty('voices')


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


video_folder = "video"
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
def main():
    # check_gpu()
    min_rate = input("Minimum rate of speech? (recommended: 180, default: 120 ) : ").strip().lower()
    if not min_rate:
        min_rate = 120

    voice_index = 2
    voice_index = input("What is the index of microsoft hindi voice? (make sure hindi voice is installed): ").strip().lower()

    if not voice_index.isdigit():
        voice_index = -1
    else:
        voice_index = int(voice_index)

    if not voice_index:
        voice_index=2
    if not voice_index < len(voices):
        print(f"Invalid voice index: {voice_index}. Available range is 0 to {len(voices)-1}")

    # Step 1: Locate video/audio file
    if not os.path.exists(video_folder):
        print(f"Folder '{video_folder}' does not exist.")
        return

    files = os.listdir(video_folder)
    target_audio_path = os.path.join(video_folder, "audio.wav")

    found_file = False
    for file in files:
        file_path = os.path.join(video_folder, file)
        if is_video_file(file):
            convert_video_to_audio(file_path, target_audio_path)
            found_file = True
            break
        elif is_audio_file(file):
            print(f"Found audio file: {file}. Copying to audio.wav.")
            shutil.copy(file_path, target_audio_path)
            found_file = True
            break

    if not found_file:
        print("No audio or video file found in the folder.")
        return

    # Step 2: Ensure demucs is installed
    check_and_install_demucs()

    # Step 3: Run demucs
    run_command(f'demucs "{target_audio_path}"')

    # Step 4: Run generateSubs.py
    run_command("python generateSubs.py")
    run_command(f'python genVoices.py {min_rate} {voice_index}')

if __name__ == "__main__":
    main()


