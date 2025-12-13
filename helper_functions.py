import streamlit as st
import os
import re
from datetime import datetime, timedelta
import wave
from genVoices import genvoices


def is_valid_srt(file_content: str) -> tuple[bool, str]:
    """
    Validate if the uploaded file is a valid .srt file.
    Returns (is_valid, error_message)
    """
    try:
        lines = file_content.strip().split('\n')
        if not lines:
            return False, "File is empty"
        
        entries = file_content.strip().split('\n\n')
        time_pattern = re.compile(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})")
        
        if len(entries) == 0:
            return False, "No subtitle entries found"
        
        valid_entries = 0
        for entry in entries:
            entry_lines = entry.split('\n')
            if len(entry_lines) >= 3:
                # Check if second line matches time pattern
                if time_pattern.match(entry_lines[1]):
                    valid_entries += 1
        
        if valid_entries == 0:
            return False, "No valid subtitle entries with correct timestamp format found"
        
        return True, ""
    except Exception as e:
        return False, f"Error parsing file: {str(e)}"


def get_duration_from_srt(file_content: str) -> float:
    """
    Extract the duration (last timestamp) from an SRT file.
    Returns duration in seconds.
    """
    try:
        time_pattern = re.compile(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})")
        
        last_end_time = None
        # Iterate through every line to find ALL timestamps and keep the last one
        for line in file_content.split('\n'):
            time_match = time_pattern.match(line.strip())
            if time_match:
                end_str = time_match.group(2)
                # Convert time string to seconds
                dt = datetime.strptime(end_str, '%H:%M:%S,%f')
                td = timedelta(hours=dt.hour, minutes=dt.minute, seconds=dt.second, microseconds=dt.microsecond)
                last_end_time = td.total_seconds()
        
        return last_end_time if last_end_time else 0
    except Exception as e:
        print(f"Error extracting duration: {e}")
        return 0


@st.fragment    
def process_audio(deep_key, google_key, uploaded_file, OK_key, OK_endpoint, gold_user, OK_model_name, female_voice, session_id, no_demucs_needed, klefki_key, speaker_lang, input_lang, main_func):
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
    
    result = main_func(session_id, deep_key, google_key, progress_bar, input_lang, no_demucs_needed, klefki_key, speaker_lang, duration, OK_key, OK_endpoint, gold_user, OK_model_name, female_voice)
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


@st.fragment
def process_subtitles(uploaded_file, input_lang, gold_user, OK_key, OK_endpoint, OK_model_name, female_voice, session_id, klefki_key):
    """
    Handles subtitle processing workflow:
    - Validates uploaded .srt file
    - Extracts duration from subtitles
    - Calls genvoices function directly
    - Displays and allows download of results
    """
    if not uploaded_file:
        st.warning("Please upload a .srt file.")
        return
    
    # Read and validate file
    file_content = uploaded_file.read().decode('utf-8')
    is_valid, error_msg = is_valid_srt(file_content)
    
    if not is_valid:
        st.error(f"❌ Invalid .srt file: {error_msg}")
        return
    
    st.success("✅ Valid .srt file detected!")
    
    # Create directories
    subs_dir = os.path.join("subtitles", session_id)
    result_dir = os.path.join("result", session_id)
    os.makedirs(subs_dir, exist_ok=True)
    os.makedirs(result_dir, exist_ok=True)
    
    # Save the uploaded file
    subs_path = os.path.join(subs_dir, f"{session_id}.srt")
    with open(subs_path, "w", encoding='utf-8') as f:
        f.write(file_content)
    
    # Extract duration from the subtitles
    duration = get_duration_from_srt(file_content)
    
    if duration == 0:
        st.warning("⚠️ Could not extract duration from subtitles.")
        return
    
    st.info(f"📊 Subtitle duration: {duration:.2f} seconds")
    
    # Process the subtitles
    st.info("Generating voiceover... Please wait.")
    progress_bar = st.progress(0)
    progress_bar.progress(50)
    
    try:
        result = genvoices(
            final_subs=subs_path,
            session_id=session_id,
            input_lang=input_lang,
            klefki_key=klefki_key,
            duration=duration,
            OK_key=OK_key,
            OK_endpoint=OK_endpoint,
            gold_user=gold_user,
            OK_model_name=OK_model_name,
            female_voice=female_voice
        )
        progress_bar.progress(100)
        
        if result == 'success':
            st.success("✅ Voiceover generation complete!")
            
            # Check if output exists
            result_path = os.path.join(result_dir, "HindiAudio.wav")
            if os.path.exists(result_path):
                with open(result_path, "rb") as audio_file:
                    audio_bytes = audio_file.read()
                    st.audio(audio_bytes, format="audio/wav")
                    
                    st.download_button(
                        label="Download Generated Audio",
                        data=audio_bytes,
                        file_name=f"voiceover_{session_id}.wav",
                        mime="audio/wav"
                    )
            else:
                st.warning("Generated audio file not found.")
        else:
            st.error(f"Processing failed: {result}")
    except Exception as e:
        st.error(f"Error during voiceover generation: {str(e)}")
        print(f"Full error: {e}")
        import traceback
        traceback.print_exc()
