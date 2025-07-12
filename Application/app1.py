import streamlit as st
import subprocess
import os
import uuid

# UI
st.title("Audio Processing App")

# 1. Secret Keys Input
secret_key_1 = st.text_input("Enter Deepgram API Key", type="password")
secret_key_2 = st.text_input("Enter Google API Key", type="password")
min_rate = st.text_input("Enter minimum rate of speech (default 180)", type="default")
voice_index = st.text_input("Enter voice index (default 2)", type="default")
print("Got keys")

# 2. File Upload
uploaded_file = st.file_uploader("Upload an audio file", type=["wav", "mp3", "m4a", "mp4"])
print("Uploaded file")

@st.fragment    
def process_audio(secret_key_1, secret_key_2, uploaded_file, min_rate, voice_index):
    """
    Handles audio processing workflow:
    - Checks for required inputs
    - Saves uploaded file
    - Sets up session directories
    - Runs prerun.py
    - Displays and allows download of results and stems
    """
    if not (secret_key_1 and secret_key_2 and uploaded_file):
        st.warning("Please provide both secret keys and upload a file.")
        return

    print("starting to process audio file")
    # Generate a unique session ID
    session_id = str(uuid.uuid4())[:8]

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

    # Pass environment variables (including session ID)
    env = os.environ.copy()
    env["API_KEY"] = secret_key_1
    env["GOOGLE_API_KEY"] = secret_key_2
    env["SESSION_ID"] = session_id

    # Run prerun.py
    st.info("Processing... Please wait.")
    result = subprocess.run(
        ["python", "prerun.py", min_rate, voice_index],
        env=env
    )

    # Check if output exists
    result_path = os.path.join(result_dir, "HindiAudio.wav")
    if os.path.exists(result_path):
        st.success("Audio processing complete!")

        # Show and allow download of main audio output
        with open(result_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
            st.audio(audio_bytes, format="audio/wav")
            # st.download_button(
            #     label="Download Processed Audio",
            #     data=audio_bytes,
            #     file_name="processed_audio.wav"
            # )

        # Download options for stems
        stems = ["bass.wav", "drums.wav", "other.wav", "vocals.wav"]
        renamed_labels = {
            "vocals.wav": "original_speech.wav",
            "bass.wav": "bass.wav",
            "drums.wav": "drums.wav",
            "other.wav": "other.wav"
        }
        for stem in stems:
            stem_path = os.path.join(stems_dir, stem)
            if os.path.exists(stem_path):
                with open(stem_path, "rb") as f:
                    file_data = f.read()
                st.audio(file_data, format="audio/wav")
                # st.download_button(
                #     label=f"Download {renamed_labels[stem]}",
                #     data=file_data,
                #     file_name=renamed_labels[stem],
                #     key=f"download_{session_id}_{stem}"
                # )
    else:
        st.error(f"Processing failed. File not found at '{result_path}'")


if st.button("Process Audio"):
    process_audio(secret_key_1, secret_key_2, uploaded_file, min_rate, voice_index)
