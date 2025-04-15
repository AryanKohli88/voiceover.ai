# voiceover.ai
Work in Progress

<!-- ----------------- -->

Run Command example- python main.py video.mp4 es

Notes - Count speakers -
Use ```ffprobe -select_streams a -show_streams outputwav_002.wav``` to check duration_ts value.
Total Number of samples = duration_ts = (total time in seconds)*(samples per second) = 44100*60 ~ 2646016
Now, hop_length for MFCC is the number of samples between two columns (frames).
=> No. of frames = 1 + 0.5*(duration_ts/hop_length) = 1+0.5*(2646016/512) = 2585

# Nyquist theorem 
To reconstruct a signal of freq w, our sampling frequency has to be > 2*w; {Note its > and not even >=};

# Next - 
Understand -  save_segmented_audio

# Progress  -
1. betterfunctions/generatesubs can generate accurate subs
2. ```demucs .\outputwav_002.wav``` will seperate tracks and vocals.  (needs - pip install demucs torchaudio soundfile and/or conda install -c conda-forge libsndfile )
3. improve seperatespeakers for seperating speakers
