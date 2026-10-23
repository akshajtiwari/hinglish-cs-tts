"""Reading audio files."""
import numpy


def load_audio(path, target_sr=None):
    """Read an audio file as a mono float32 waveform. Tries soundfile first, then librosa for other formats."""
    try:
        import soundfile
        wav, sr = soundfile.read(path, dtype="float32", always_2d=True)
        wav = wav.mean(axis=1)
    except Exception:
        import librosa
        wav, sr = librosa.load(path, sr=None, mono=True)
    if target_sr and sr != target_sr:
        import librosa
        wav = librosa.resample(wav, orig_sr=sr, target_sr=target_sr)
        sr = target_sr
    return numpy.ascontiguousarray(wav, dtype="float32"), sr
