import streamlit as st
import subprocess
import os
import time

# UI
st.title("Audio Processing App")

# 1. Secret Keys Input
secret_key_1 = st.text_input("Enter Secret Key 1", type="password")
secret_key_2 = st.text_input("Enter Secret Key 2", type="password")

# 2. File Upload
uploaded_file = st.file_uploader("Upload an audio file", type=["wav", "mp3", "m4a"])

# 3. Submit Button
if st.button("Process Audio"):
    if not (secret_key_1 and secret_key_2 and uploaded_file):
        st.warning("Please provide both secret keys and upload a file.")
    else:
        # Save the uploaded file temporarily
        with open("input_audio.wav", "wb") as f:
            f.write(uploaded_file.read())

        # Optional: Pass secrets as environment variables if needed
        env = os.environ.copy()
        env["API_KEY"] = secret_key_1
        env["GOOGLE_API_KEY"] = secret_key_2

        # 4. Run prerun.py in background
        st.info("Processing... Please wait.")
        result = subprocess.run(["python", "prerun.py"], env=env)

        # 5. Check if output exists
        result_path = "result/audio.wav"
        if os.path.exists(result_path):
            st.success("Audio processing complete!")
            audio_file = open(result_path, "rb")
            audio_bytes = audio_file.read()
            st.audio(audio_bytes, format="audio/wav")
            st.download_button(label="Download Audio", data=audio_bytes, file_name="processed_audio.wav")
        else:
            st.error("Processing failed. 'result/audio.wav' not found.")
