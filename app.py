import streamlit as st
import subprocess
import os
import uuid
import requests
import time
from prerun import main_func
import tempfile
import re
from datetime import datetime, timedelta
from genVoices import genvoices
from helper_functions import is_valid_srt, get_duration_from_srt, process_audio, process_subtitles

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
st.markdown("Get your own <a href='https://klefkikeys.netlify.app/' target='_blank'><strong>Klefki Key</strong></a>.", unsafe_allow_html=True)

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

st.divider()

# --- Input Type Selection ---
input_type = st.radio(
    "What do you have?",
    options=["I have audio (.wav)", "I have subtitles (.srt)"],
    horizontal=True
)


# 1. Secret Keys Input
deep_key = st.secrets["DEEPGRAM_KEY"]
OK_key = st.secrets["OK_KEY"]
OK_endpoint = st.secrets["OK_ENDPOINT"]
OK_model_name = st.secrets["OK_MODEL_NAME"]

google_key = st.secrets["GOOGLE_KEY"] # st.text_input("Enter Google API Key", type="password")
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

# --- Show different options based on input type ---
if input_type == "I have audio (.wav)":
    no_demucs_needed = False
    no_demucs_needed = st.checkbox(
        "Don't separate background music or noise. [Recomended for faster response - Reduces time taken by half!]",
        disabled=os.path.exists(LOCK_FILE)
    )
    
    PREMIUM_LANGUAGES = {
        "English",
        "Hindi",
        "Bengali",
        "Malayalam",
        "Marathi",
        "Tamil",
        "Gujarati",
        "Telugu",
        "Kannada",
    }
    premium_allowed = input_lang in PREMIUM_LANGUAGES
    if not premium_allowed:
        st.session_state["gold_user"] = False

    gold_user = st.checkbox(
        "Premium Quality Voice", # add link to pricing and other details
        key="gold_user",
        disabled=not premium_allowed
    )
    if not premium_allowed:
        st.warning("⚠️ Premium voice is not available for the selected language.")

    female_voice = False
    if gold_user:
        female_voice = st.checkbox(
            "Use Female Voice",
            key="female_voice",
            value=False
        )

    min_rate_ip = 180 # st.text_input("Enter minimum rate of speech (Recommended value - 180)", type="default")

    # 2. File Upload
    uploaded_file = st.file_uploader("Upload an audio file", type=["wav"])

else:  # I have subtitles
    no_demucs_needed = True
    
    PREMIUM_LANGUAGES = {
        "English",
        "Hindi",
        "Bengali",
        "Malayalam",
        "Marathi",
        "Tamil",
        "Gujarati",
        "Telugu",
        "Kannada",
    }
    premium_allowed = input_lang in PREMIUM_LANGUAGES
    if not premium_allowed:
        st.session_state["gold_user"] = False

    gold_user = st.checkbox(
        "Premium Quality Voice", # add link to pricing and other details
        key="gold_user",
        disabled=not premium_allowed
    )
    if not premium_allowed:
        st.warning("⚠️ Premium voice is not available for the selected language.")

    female_voice = False
    if gold_user:
        female_voice = st.checkbox(
            "Use Female Voice",
            key="female_voice",
            value=False
        )
    
    # File Upload for subtitles
    uploaded_file = st.file_uploader("Upload your subtitles", type=["srt"])


if st.button("Process Audio" if input_type == "I have audio (.wav)" else "Generate Audio"):

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

    if input_type == "I have audio (.wav)":
        process_audio(deep_key, google_key, uploaded_file, OK_key, OK_endpoint, gold_user, OK_model_name, female_voice, session_id, no_demucs_needed, klefki_key, speaker_lang, input_lang, main_func)
    else:
        process_subtitles(uploaded_file, input_lang, gold_user, OK_key, OK_endpoint, OK_model_name, female_voice, session_id, klefki_key)
