import librosa
import numpy as np
from sklearn.cluster import AgglomerativeClustering
import soundfile as sf
import os
import matplotlib.pyplot as plt

def extract_mfcc(audio_file):
    """
    Extracts MFCC features from an audio file.

    Args:
        audio_file (str): Path to the audio file.

    Returns:
        numpy.ndarray: MFCC features (num_frames x num_coefficients).  Returns an empty array on error.
    """
    try:
        audio, sample_rate = librosa.load(audio_file)
        mfcc = librosa.feature.mfcc(y=audio, sr=sample_rate, hop_length=512)
        # Transpose MFCC to have shape (num_frames, num_coefficients)
        # eariler n MFCC Vectors, each vector has m elements, each element for one frame.
        # after transpose, ith vector will be MFCC coeffients of ith frame.
        # returned shape is (2585 frames,20 features) -> 
        return mfcc.T 
        # return mfcc
    except Exception as e:
        print(f"Error extracting MFCCs: {e}")
        return np.array([])

def count_speakers(audio_file, n_clusters=2):
    """
    Counts speakers in an audio file using MFCCs and clustering.

    Args:
        audio_file (str): Path to the audio file.
        n_clusters (int, optional): Number of clusters (speakers) to find. Defaults to 2.

    Returns:
        int: Number of speakers detected.
    """
    mfcc_features = extract_mfcc(audio_file)

    if mfcc_features.size == 0:
        return 0  # Handle the error case from extract_mfcc

    # Cluster the MFCC features using Agglomerative Clustering
    cluster = AgglomerativeClustering(n_clusters=n_clusters) # clubs the mfcc vectors into n clusters
    cluster_labels = cluster.fit_predict(mfcc_features)

    # The number of unique labels is the number of speakers.
    num_speakers = len(np.unique(cluster_labels))
    return num_speakers

def save_segmented_audio(audio_file, cluster_labels, n_clusters):
    """
    Segments the audio file based on speaker clusters and saves each segment.

    Args:
        audio_file (str): Path to the input audio file.
        cluster_labels (numpy.ndarray): Cluster labels for each frame.
        n_clusters (int): The number of clusters (speakers).
    """
    try:
        audio, sample_rate = librosa.load(audio_file)
        frame_length = 2048  # Typical frame length for MFCC
        hop_length = 512    # Typical hop length
        
        # Calculate frame boundaries in samples
        frame_boundaries = np.arange(0, len(cluster_labels) * hop_length, hop_length)
        
        # Ensure frame_boundaries does not exceed audio length.
        frame_boundaries = frame_boundaries[:len(cluster_labels)]

        for i in range(n_clusters):
            # Get the indices of the frames belonging to cluster i
            cluster_frames_indices = np.where(cluster_labels == i)[0]
            
            # Get the start and end sample for the cluster.  Use frame boundaries.
            start_sample = frame_boundaries[cluster_frames_indices[0]]
            end_sample = frame_boundaries[cluster_frames_indices[-1]] + frame_length # add frame_length to include the last part
            
            # Extract the audio segment for the cluster.  Important:  Limit to audio length.
            segment = audio[start_sample:min(end_sample, len(audio))]
            
            # Handle empty segments
            if len(segment) > 0:
                # Save the segment to a new audio file
                output_file = f"speaker_{i+1}_segment.wav"
                sf.write(output_file, segment, sample_rate)
                print(f"Saved segment: {output_file}")
            else:
                print(f"Skipped empty segment for speaker {i+1}")

    except Exception as e:
        print(f"Error saving segmented audio: {e}")

if __name__ == "__main__":
    audio_file = "../separated/htdemucs/outputwav_002/vocals.wav"  # Replace with your audio file
    num_speakers = 3  #initial guess, adjust

    # Create a dummy audio file for testing if "audio.wav" does not exist
    if not os.path.exists(audio_file):
        print(f"Creating a dummy audio file: {audio_file}")
        # Create a silent audio file for 2 seconds at 16000 Hz
        silent_audio = np.zeros(16000 * 2, dtype=np.float32)
        sf.write(audio_file, silent_audio, 16000)

    speaker_count = count_speakers(audio_file, num_speakers)
    if speaker_count > 0:
        print(f"Number of speakers: {speaker_count}")
        
        #save segemented audio.
        cluster_labels = np.zeros(100) #dummy cluster labels.  Replace with actual labels from a clustering algorithm
        save_segmented_audio(audio_file, cluster_labels, num_speakers)
    else:
        print("No speakers detected or error occurred.")

    # mfcc_vectors = extract_mfcc(audio_file)
    # print(mfcc_vectors.shape)
 

    # # Create tick positions and labels for first 7 seconds and first 4 coefficients
    # num_frames = mfcc_vectors.shape[1]
    # x = np.arange(num_frames)
    # num_frames = 7  
    # num_ticks = 7   
    # tick_positions = np.arange(num_frames)  
    # tick_labels = np.linspace(0, 7, num_ticks, dtype=int)  # Spread 0-7 over 7 ticks

    # plt.figure(figsize=(15, 6))
    # for i in range(4):  # only first 4 MFCCs
    #     plt.plot(x[:7], mfcc_vectors[i][:7], label=f'MFCC {i+1}')  # only first 7 values
    # plt.xlabel('Time (s)')
    # plt.ylabel('Coefficient Value')
    # plt.title('MFCCs over Time (First 7 Frames)')
    # plt.xticks(tick_positions[:7], tick_labels[:7])  # Adjust x-axis ticks accordingly
    # plt.grid(True)
    # plt.legend()
    # plt.tight_layout()
    # plt.show()