# voiceover.ai
Work in Progress

<!-- ----------------- -->

Run Command example- python main.py video.mp4 es

Notes - Count speakers -
Use ```ffprobe -select_streams a -show_streams outputwav_002.wav``` to check duration_ts value.
Total Number of samples = duration_ts = (total time in seconds)*(samples per second) = 60*44100 ~ 2646016
The hop length in audio processing defines how many samples to advance between consecutive frames
Now, hop_length for MFCC is the number of samples between two columns (frames).
num_frames = 1 + int((total_time * sample_rate - frame_length) / hop_length)

# Nyquist theorem 
To reconstruct a signal of freq w, our sampling frequency has to be > 2*w; {Note its > and not even >=};

# Next - 
Understand -  save_segmented_audio

# Progress  -
1. betterfunctions/generatesubs can generate accurate subs
2. ```demucs .\outputwav_002.wav``` will seperate tracks and vocals.  (needs - pip install demucs torchaudio soundfile and/or conda install -c conda-forge libsndfile )
3. improve seperatespeakers for seperating speakers

# Steps
1. Get Clean Vocals -  ```demucs .\outputwav_002.wav```
2. test.py to seperate speakers
3. gernerateSubs.js to generate subs
4. generate audio from srt - todo