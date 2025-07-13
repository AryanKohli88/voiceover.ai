import os
import subprocess
import sys
import torch
import shutil
from generateSubs import transcribe_file
from genVoices import genvoices


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
        print("Demucs is already installed.")
    except FileNotFoundError:
        print("Demucs not found. Installing...")
        run_command("pip install demucs")
        return 'Demucs not found. Please try again after 20 minutes'

# -------------------------------
# Main Logic
# -------------------------------
def is_valid_integer(value):
    return value.isdigit() and int(value) > 0

def main_func(min_rate_ip, session_id, deep_key, google_key, progress_bar):
    if not is_valid_integer(min_rate_ip):
        return 'invalid values for <min_rate>'
    
    min_rate = int(min_rate_ip)

    video_dir = os.path.join("video", session_id)

    print(f"Using value {min_rate} for {session_id}")

    target_audio_path = os.path.join(video_dir, f"{session_id}.wav")
    print("Using Demucs")
    progress_bar.progress(10)

    check_and_install_demucs()

    run_command(f'demucs "{target_audio_path}"')
    print("Demucsing completed")
    progress_bar.progress(40)

    # TO DELETE original audio file
    if os.path.exists(video_dir):
        try:
            shutil.rmtree(video_dir)
            print(f"Deleted existing directory: {video_dir}")
        except Exception as e:
            print(f"Could not delete existing directory: {e}")

    # Step 4: Run generateSubs.py
    print("calling generate subs")
    
    t_subs_path = f"./separated/htdemucs/{session_id}"
    op = transcribe_file(f"{t_subs_path}/{session_id}_translated.srt", session_id, deep_key, google_key, progress_bar)
    progress_bar.progress(80)
    
    if(op.strip().lower() != 'success'):
        return op
    print(f'completed generate subs at - {t_subs_path}')

    progress_bar.progress(90)
    genvoices(f"{t_subs_path}/{session_id}_translated.srt", min_rate, session_id)
    progress_bar.progress(100)

    # if os.path.exists(t_subs_path):
    #     try:
    #         shutil.rmtree(t_subs_path)
    #         print(f"Deleted existing directory: {t_subs_path}")
    #     except Exception as e:
    #         print(f"Could not delete existing directory: {e}")
