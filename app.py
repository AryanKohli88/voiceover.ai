import streamlit as st
import subprocess
import os
import uuid
from prerun import main_func
import os

st.title("Translate to hindi")
session_id = str(uuid.uuid4())[:8]
os.environ["PATH"] = os.path.abspath("ffmpeg") + os.pathsep + os.environ["PATH"]

# 1. Secret Keys Input
deep_key = st.text_input("Enter Deepgram API Key", type="password")
google_key = st.text_input("Enter Google API Key", type="password")
min_rate_ip = st.text_input("Enter minimum rate of speech (Recommended value - 180)", type="default")
# voice_index_ip = st.text_input("Enter voice index (Recommended value - 2)", type="default")

# 2. File Upload
uploaded_file = st.file_uploader("Upload an audio file", type=["wav", "mp3", "m4a", "mp4"])


@st.fragment    
def process_audio(deep_key, google_key, uploaded_file, min_rate_ip):
    """
    Handles audio processing workflow:
    - Checks for required inputs
    - Saves uploaded file
    - Sets up session directories
    - Runs prerun.py
    - Displays and allows download of results and stems
    """
    if not (deep_key and google_key and uploaded_file and min_rate_ip):
        st.warning("Please provide all values and upload a file.")
        return

    print("starting to process audio file")

    # Define directories based on session ID
    video_dir = os.path.join("video", session_id)
    result_dir = os.path.join("result", session_id)
    stems_dir = os.path.join("separated", "htdemucs", session_id)

    # Create directories
    os.makedirs(video_dir, exist_ok=True)
    os.makedirs(result_dir, exist_ok=True)
    os.makedirs(stems_dir, exist_ok=True)

    # Save the uploaded file to ./video/<session_id>/<session_id>.wav
    input_path = os.path.join(video_dir, f"{session_id}.wav")
    with open(input_path, "wb") as f:
        f.write(uploaded_file.read())

    # Run prerun.py
    st.info("Processing... Please wait.")
    progress_bar = st.progress(0)

    result = main_func(min_rate_ip, session_id, deep_key, google_key, progress_bar)
    st.info(result)
        
    # Check if output exists
    result_path = os.path.join(result_dir, "HindiAudio.wav")
    if os.path.exists(result_path):
        st.success("Audio processing complete!")

        # Show and allow download of main audio output
        with open(result_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
            st.audio(audio_bytes, format="audio/wav")

        # Download options for stems
        stems = ["bass.wav", "drums.wav", "other.wav", "vocals.wav"]
        # renamed_labels = {
        #     "vocals.wav": "original_speech.wav",
        #     "bass.wav": "bass.wav",
        #     "drums.wav": "drums.wav",
        #     "other.wav": "other.wav"
        # }
        for stem in stems:
            stem_path = os.path.join(stems_dir, stem)
            if os.path.exists(stem_path):
                with open(stem_path, "rb") as f:
                    file_data = f.read()
                st.audio(file_data, format="audio/wav")
            else:
                print("stem doesn't exist")
    else:
        st.error(f"Processing failed. File not found at '{result_path}'. \nIn case of any issue please save this sessions id - {session_id}. This helps.")


if st.button("Process Audio"):
    process_audio(deep_key, google_key, uploaded_file, min_rate_ip)
