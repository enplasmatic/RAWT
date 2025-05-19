from pedalboard import *
from pedalboard.io import AudioFile
from scipy.signal import resample
import librosa
import soundfile as sf
import pedalboard
import numpy as np
import soundfile as sf
from scipy.signal import sosfilt, sosfilt_zi, sosfreqz
from scipy.signal import iirfilter

import numpy as np
from scipy.signal import butter, sosfilt
import numpy as np

from scipy.io import wavfile

def pan_audio(audio, pan):
    """
    Pan audio left (-1.0) to right (+1.0). Assumes mono input.
    Returns stereo (2-channel) output.
    
    :param audio: 1D numpy array (mono audio)
    :param pan: float from -1.0 (left) to +1.0 (right)
    """
    pan = np.clip(pan, -1.0, 1.0)
    left_gain = np.cos((pan + 1) * np.pi / 4)
    right_gain = np.sin((pan + 1) * np.pi / 4)

    stereo = np.vstack((audio * left_gain, audio * right_gain)).T
    return stereo


def wah_wah_sfx(audio, sr, depth=0.7, rate=2.0, base_freq=300, max_freq=1500, q=0.6):
    """
    Wah-wah effect without scipy. Clean, fat, and efficient.
    
    Parameters:
    - audio: NumPy array of mono audio
    - sr: Sample rate (e.g., 44100)
    - depth: Sweep range intensity (0 to 1)
    - rate: Sweep speed (Hz)
    - base_freq: Minimum center frequency
    - max_freq: Maximum center frequency
    - q: Resonance (0.4 to 1.0 for clean sound)
    
    Returns:
    - Modified audio with wah-wah effect
    """
    # Ensure mono
    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    samples = len(audio)
    t = np.linspace(0, samples / sr, samples)
    
    # Generate LFO sweep for center frequencies
    sweep = (np.sin(2 * np.pi * rate * t) + 1) / 2
    center_freqs = base_freq + sweep * depth * (max_freq - base_freq)
    
    # Initialize output and filter states
    out = np.zeros_like(audio)
    y1, y2 = 0.0, 0.0
    x1, x2 = 0.0, 0.0

    for i in range(samples):
        f0 = center_freqs[i]
        omega = 2 * np.pi * f0 / sr
        alpha = np.sin(omega) / (2 * q)
        
        # Bandpass filter coefficients (constant skirt gain)
        b0 = alpha
        b1 = 0.0
        b2 = -alpha
        a0 = 1 + alpha
        a1 = -2 * np.cos(omega)
        a2 = 1 - alpha

        # Normalize coefficients
        b0 /= a0
        b1 /= a0
        b2 /= a0
        a1 /= a0
        a2 /= a0

        x0 = audio[i]
        y0 = b0 * x0 + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2

        out[i] = y0

        # Update delay elements
        x2 = x1
        x1 = x0
        y2 = y1
        y1 = y0

    # Normalize to avoid clipping
    out /= np.max(np.abs(out) + 1e-9)

    return out



def BOUND(v, h, l):
    return l + (h - l) * (v / 100)
    
def apply(e, PATH):
    # Load audio
    pp2 = PATH
    pp = PATH
    if e["Wah q"] > 0:
        audio, sr = sf.read(PATH)
        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        audio = wah_wah_sfx(audio, sr, depth=BOUND(e["Wah Depth"], 0.5, 1), rate=BOUND(e["Wah Rate"], 1, 6), base_freq=BOUND(e["Wah Drive"], 300, 500), q=BOUND(e["Wah q"], 0.5, 0.8))
        sf.write("output.wav", audio, sr)
        pp = 'output.wav'

    rate, data = wavfile.read(pp)
    if data.ndim > 1:
        data = data.mean(axis=1)  # convert to mono if stereo

    data = data.astype(np.float32)
    data /= np.max(np.abs(data))  # normalize

    stereo_panned = pan_audio(data, pan=BOUND(100-e["Pan"], -1, 1)) 
    wavfile.write("output.wav", rate, (stereo_panned * 32767).astype(np.int16))

    data, samplerate = sf.read("output.wav")


    # Speed factor
    speed = (e["Speed"]*5) * 0.01  # e.g., 1.5x faster

    # Resample to new number of samples
    num_samples = int(len(data) / max(0.01, speed))
    data_resampled = resample(data, num_samples)

    # Save to new file
    sf.write('output.wav', data_resampled, samplerate)
    pp2 = 'output.wav'

    # Load the input WAV file
    with AudioFile(pp2) as f:
        audio = f.read(f.frames)  # Get audio as numpy array
        samplerate = f.samplerate

    

    # Create a pedalboard (chain of effects)
    eff = [
        Reverb(room_size=e["Reverb Size"]*0.01, damping=e["Reverb Damping"]*0.01, 
               wet_level=e["Wet Level"]*0.01, dry_level=e["Dry Level"]*0.01, width=e["Reverb Width"]*0.01, 
               ),
        Delay(delay_seconds=e["Delay in Seconds"]*0.04, feedback=e["Delay Feedback"]*0.01, mix=e["Delay Mix"]*0.01),
        Bitcrush(bit_depth=e["Bitcrush Mix"]*0.16),

        Gain(gain_db=(e["Gain / Volume"]-50) * 1.2),
        HighpassFilter(cutoff_frequency_hz=e["Highpass"]*60),
        LowpassFilter(cutoff_frequency_hz=e["Lowpass"]*30),

        Distortion(drive_db=e["Drive"]*0.6),
        PitchShift(semitones=(e["Pitch"]-50) * 0.24),
        Limiter(threshold_db=(e["Limiter DB"]-100), release_ms=e["Limiter Release"]*10),

        Chorus(rate_hz=max(0.01, e["LFO Speed"]*0.1),
               depth=e["LFO Detune"]*0.002, centre_delay_ms=e["Base Delay"], feedback=e["Chorus Feedback"]*0.01, mix=e["Chorus Mix"]*0.01),
    
        Phaser(rate_hz=max(0.01, e["Sweep Speed"]*0.05),
               depth=e["Sweep Detune"]*0.01, centre_frequency_hz=e["Sweep Delay"]*20, feedback=e["Sweep Feedback"]*0.01, mix=e["Sweep Mix"]*0.01),
        
        Compressor(threshold_db=e["Thresh"]*-0.01, ratio=max(1, e["Comp Ratio"]*0.2), attack_ms=e["Comp Attack"]*5, release_ms=e["Comp Release"]*20), # Punch
        
        NoiseGate(threshold_db=e["NG Thresh"]*-0.01, ratio=max(1, e["NG Ratio"]*0.2), attack_ms=e["NG Attack"]*5, release_ms=e["NG Release"]*20), 
        LowShelfFilter(cutoff_frequency_hz=(e["F Ratio"]*4.8) + 20, gain_db=(e["F Attack"]-50)*0.24, q=e["Q"]*0.01),
        HighShelfFilter(cutoff_frequency_hz=(e["F Thresh"]*18)+2000, gain_db=(e["F Release"]-50)*0.24, q=e["Q"]*0.01),

    ]

    if e["Invert"] >= 50:
        eff.append(Invert())
    board = Pedalboard(eff)



    # Apply the effects
    processed = board(audio, samplerate)

    # Save the output to a new WAV file
    with AudioFile('output.wav', 'w', samplerate, audio.shape[0]) as f:
        f.write(processed)

import os
import shutil
import tkinter as tk
from tkinter import filedialog
def dnld():
    source_file = 'output.wav'  # or a full path like '/path/to/example.wav'
    downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
    destination = os.path.join(downloads_folder, os.path.basename(source_file))
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    file_path = filedialog.asksaveasfilename(
        defaultextension=".wav",
        filetypes=[("Wave files", "*.wav"), ("All files", "*.*")]
    )

    if file_path:
        shutil.copy(source_file, file_path)

        print(f"File saved at: {file_path}")
    else:
        print("No file selected.")

    print("Downloaded")
