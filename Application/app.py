import streamlit as st
import subprocess
import os
from pathlib import Path
import shutil

st.set_page_config(page_title="Voice Cloning Inference", layout="centered")
st.title("🎙️ Voice Cloning Inference UI")

st.markdown("Upload an audio file, select a model, and run inference.")

# File upload
uploaded_audio = st.file_uploader("Upload WAV audio file", type=["wav"])
uploaded_model = st.file_uploader("Upload .pth model file", type=["pth"])
uploaded_config = st.file_uploader("Upload config.json", type=["json"])

# Prepare directories
TEMP_DIR = Path("temp_inputs")
TEMP_DIR.mkdir(exist_ok=True)

def save_uploaded_file(uploaded_file, save_path):
    with open(save_path, "wb") as f:
        f.write(uploaded_file.read())

# Run inference
if st.button("Run Inference"):
    if not (uploaded_audio and uploaded_model and uploaded_config):
        st.warning("Please upload all required files.")
    else:
        audio_path = TEMP_DIR / "input.wav"
        model_path = TEMP_DIR / "model.pth"
        config_path = TEMP_DIR / "config.json"

        # Save files
        save_uploaded_file(uploaded_audio, audio_path)
        save_uploaded_file(uploaded_model, model_path)
        save_uploaded_file(uploaded_config, config_path)

        # Inference command
        output_dir = TEMP_DIR / "output"
        output_dir.mkdir(exist_ok=True)

        output_audio = output_dir / "converted.wav"

        command = f"svc infer {audio_path} -m {model_path} -c {config_path} -o {output_audio}"

        with st.spinner("Running inference..."):
            try:
                result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
                st.success("Inference complete!")

                if output_audio.exists():
                    st.audio(str(output_audio))
                    with open(output_audio, "rb") as f:
                        st.download_button("Download Output", f, file_name="converted.wav")
                else:
                    st.error("Output file not generated.")
                    st.text(result.stdout)
                    st.text(result.stderr)

            except subprocess.CalledProcessError as e:
                st.error("Inference failed.")
                st.text(e.stdout)
                st.text(e.stderr)

# Clean up option
if st.checkbox("Clean temporary files after run"):
    shutil.rmtree(TEMP_DIR)
    st.success("Temporary files deleted.")
