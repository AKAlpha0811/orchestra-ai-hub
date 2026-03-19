import tempfile

import librosa
import numpy as np
import soundfile as sf


def normalize_tempo_value(raw_tempo) -> int:
    """
    Convert librosa tempo output into one safe integer BPM value.

    Depending on the library version, beat_track may return a float,
    a 0-D numpy value, or a small numpy array.
    """
    if raw_tempo is None:
        return 0

    tempo_array = np.asarray(raw_tempo).reshape(-1)

    if tempo_array.size == 0:
        return 0

    return int(round(float(np.mean(tempo_array))))


def load_audio_as_wav(audio_path: str, target_sample_rate: int = 22050) -> tuple[np.ndarray, int, str]:
    """
    Load audio with librosa and save a normalized WAV copy.

    This makes later analysis simpler because every input format ends up
    using the same sample rate, mono channel layout, and file type.
    """
    audio_data, sample_rate = librosa.load(audio_path, sr=target_sample_rate, mono=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
        sf.write(temp_wav.name, audio_data, sample_rate)
        return audio_data, sample_rate, temp_wav.name


def calculate_beat_intervals(beat_times: np.ndarray) -> np.ndarray:
    """Return the time gap between each detected beat."""
    if len(beat_times) < 2:
        return np.array([])
    return np.diff(beat_times)


def describe_consistency(intervals: np.ndarray) -> tuple[str, float]:
    """
    Measure how stable the beat spacing is.

    The coefficient of variation is a simple way to compare spread:
    smaller numbers mean more even rhythm.
    """
    if len(intervals) == 0:
        return "Not enough beat data", 0.0

    mean_interval = float(np.mean(intervals))
    if mean_interval == 0:
        return "Not enough beat data", 0.0

    variation_ratio = float(np.std(intervals) / mean_interval)

    if variation_ratio < 0.08:
        return "Very steady", variation_ratio
    if variation_ratio < 0.16:
        return "Mostly steady", variation_ratio
    if variation_ratio < 0.25:
        return "A little uneven", variation_ratio
    return "Needs more steady pulse", variation_ratio


def describe_tempo_trend(intervals: np.ndarray) -> str:
    """Compare the first half and second half of the beat intervals."""
    if len(intervals) < 4:
        return "Not enough data to detect a tempo trend"

    midpoint = len(intervals) // 2
    first_half = intervals[:midpoint]
    second_half = intervals[midpoint:]

    if len(first_half) == 0 or len(second_half) == 0:
        return "Not enough data to detect a tempo trend"

    first_average = float(np.mean(first_half))
    second_average = float(np.mean(second_half))
    change_ratio = (second_average - first_average) / first_average

    if change_ratio > 0.08:
        return "The tempo gets slower later in the recording"
    if change_ratio < -0.08:
        return "The tempo gets faster later in the recording"
    return "The overall tempo stays fairly stable"


def build_feedback(estimated_bpm: int, consistency_label: str, tempo_trend: str) -> list[str]:
    """Create short student-friendly feedback messages."""
    feedback = [f"Your estimated tempo is around {estimated_bpm} BPM."]

    if consistency_label == "Very steady":
        feedback.append("Your beat is very consistent. Keep this steady pulse.")
    elif consistency_label == "Mostly steady":
        feedback.append("Your rhythm is mostly stable with a few small timing changes.")
    elif consistency_label == "A little uneven":
        feedback.append("Some beats are uneven. Try practicing slowly with a metronome.")
    else:
        feedback.append("Your pulse changes quite a lot. Focus on keeping equal beat spacing.")

    if "slower" in tempo_trend:
        feedback.append("You tend to slow down. Try counting out loud through long notes and rests.")
    elif "faster" in tempo_trend:
        feedback.append("You tend to speed up. Try relaxing and letting the beat lead your playing.")
    elif "stable" in tempo_trend:
        feedback.append("Your tempo direction stays fairly stable across the recording.")
    else:
        feedback.append("There was not enough beat information to judge tempo direction clearly.")

    feedback.append("This is a simple rhythm coach, so use the result as a practice guide, not a final musical judgment.")
    return feedback


def analyze_practice_audio(audio_path: str) -> dict:
    """
    Analyze a student recording and return simple rhythm feedback.

    The analysis is intentionally simple and demo-friendly:
    it estimates tempo, compares beat spacing, and checks whether the
    performance speeds up or slows down over time.
    """
    audio_data, sample_rate, normalized_wav_path = load_audio_as_wav(audio_path)

    if len(audio_data) == 0:
        raise ValueError("The uploaded audio file is empty.")

    onset_envelope = librosa.onset.onset_strength(y=audio_data, sr=sample_rate)

    if np.max(np.abs(onset_envelope)) == 0:
        raise ValueError("The recording is too quiet or unclear for beat analysis.")

    tempo, beat_frames = librosa.beat.beat_track(
        onset_envelope=onset_envelope,
        sr=sample_rate,
    )
    beat_times = librosa.frames_to_time(beat_frames, sr=sample_rate)
    beat_intervals = calculate_beat_intervals(beat_times)

    estimated_bpm = normalize_tempo_value(tempo)
    consistency_label, variation_ratio = describe_consistency(beat_intervals)
    tempo_trend = describe_tempo_trend(beat_intervals)
    feedback = build_feedback(estimated_bpm, consistency_label, tempo_trend)

    return {
        "estimated_bpm": estimated_bpm,
        "consistency_label": consistency_label,
        "variation_ratio": round(variation_ratio, 3),
        "tempo_trend": tempo_trend,
        "feedback": feedback,
        "normalized_wav_path": normalized_wav_path,
    }
