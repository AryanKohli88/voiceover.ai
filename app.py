import streamlit as st
import subprocess
import os
import uuid
import requests
import time
from prerun import main_func
import os
import streamlit as st
import wave
import tempfile

# from test import test_generate_voice_overs
# from genVoices import parse_srt_file
st.set_page_config(
    page_title="Klefki AI Translator",
    page_icon="🎙️",
    layout="wide"
)

st.title("Dub your audio with Klefki's AI Powered Audio Translator 🎙️🌐")
session_id = str(uuid.uuid4())[:8]
os.environ["PATH"] = os.path.abspath("ffmpeg") + os.pathsep + os.environ["PATH"]

# --- 0. Test Klefki Key ---
st.markdown("📘 Watch the <a href='https://aryankohli88.github.io/tfypdubs.html' target='_blank'><strong>Tutorial</strong></a> on how to use this tool.", unsafe_allow_html=True)

klefki_key = st.text_input("Enter your Klefki API Key", type="password")
test_button = st.button("Test My Key")

if test_button and klefki_key:
    with st.spinner("Verifying your key..."):
        try:
            response = requests.get(
                "https://klefki-backend-fra.onrender.com/api/validate/ukk",  # replace with your actual endpoint
                json={"key": klefki_key},
                timeout=10
            )
            if response.status_code == 200:
                st.success("✅ Key is valid!")
            else:
                st.error(f"❌ Invalid key! Server responded with status {response.status_code}")
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Error connecting to server: {e}")


# 1. Secret Keys Input
deep_key = st.secrets["DEEPGRAM_KEY"]
OK_key = st.secrets["OK_KEY"]
OK_endpoint = st.secrets["OK_ENDPOINT"]
OK_model_name = st.secrets["OK_MODEL_NAME"]

google_key = st.text_input("Enter Google API Key", type="password")
input_lang = st.radio(
    "Select output language:",
    options=[
        ("hi", "Hindi"), # enable for gold users accordingly
        ("bn", "Bengali"),
        ("ta", "Tamil"),
        ("te", "Telugu"),
        ("ml", "Malayalam"),
        ("kn", "Kannada"),
        ("gu", "Gujarati"),
        ("mr", "Marathi"),
        ("pa", "Punjabi"),
        ("ur", "Urdu"),
        ("ne", "Nepali"),
        ("si", "Sinhala"),
        ("en", "English"),
        ("fr", "French"),
        ("zh-CN", "Mandarin (China Mainland)"),
        ("zh-TW", "Mandarin (Taiwan)"),
        ("pt", "Portuguese"),
        ("es", "Spanish")
    ],
    format_func=lambda x: x[1]
)[1]  # Extract only the language name

speaker_lang = st.radio(
    "Select input language:",
    options=[
        ("hi", "Hindi"),
        ("en", "English")
    ],
    format_func=lambda x: x[1]
)[0]  # Extract only the language code

tmp_dir = tempfile.gettempdir()  # usually /tmp on Linux, correct on Windows too
LOCK_FILE = os.path.join(tmp_dir, "demucs.lock")

no_demucs_needed = False
no_demucs_needed = st.checkbox(
    "I do not need backgroud music as a seperate file / I have clean audio with no background noise. (Reduces time taken to half!)",
    disabled=os.path.exists(LOCK_FILE)
)

gold_user = st.checkbox("Premium Quality Voice")
# gold_user = st.checkbox("Premium Quality Voide (Comming Soon!)", disabled=True)
min_rate_ip = 180 # st.text_input("Enter minimum rate of speech (Recommended value - 180)", type="default")

# 2. File Upload
uploaded_file = st.file_uploader("Upload an audio file", type=["wav"])


@st.fragment    
def process_audio(deep_key, google_key, uploaded_file, OK_key, OK_endpoint, gold_user, OK_model_name):
    """
    Handles audio processing workflow:
    - Checks for required inputs
    - Saves uploaded file
    - Sets up session directories
    - Runs prerun.py
    - Displays and allows download of results and stems
    """
    if not (deep_key and google_key and uploaded_file):
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

    duration = 0
    with wave.open(input_path, "rb") as audio:
        duration = audio.getnframes() / audio.getframerate()

    # Run prerun.py
    st.info("Processing... Please wait.")
    progress_bar = st.progress(0)
    
    result = main_func(session_id, deep_key, google_key, progress_bar, input_lang, no_demucs_needed, klefki_key, speaker_lang, duration, OK_key, OK_endpoint, gold_user, OK_model_name)
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

    with st.spinner("Verifying your key..."):
        try:
            response = requests.get(
                "https://klefki-backend-fra.onrender.com/api/validate/ukk",  # replace with your actual endpoint
                json={"key": klefki_key},
                timeout=10
            )
            if response.status_code == 200:
                st.success("✅ Key is valid!")
            else:
                st.error(f"❌ Invalid key! Server responded with status {response.status_code}")
                st.stop()
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Error connecting to server: {e}")
            st.stop()


    process_audio(deep_key, google_key, uploaded_file, OK_key, OK_endpoint, gold_user, OK_model_name)
    # newsubs_parsed = parse_srt_file('./test_subs.srt')
    # test_generate_voice_overs(newsubs_parsed, "./HindiAudio.wav", 180, 111)
    # st.audio('./result/111/HindiAudio.wav', format="audio/wav")
    # print("done")
