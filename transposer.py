import tempfile

from music21 import converter, instrument, interval, note


# This list is used by the Streamlit UI, so keep the labels user-friendly.
SUPPORTED_INSTRUMENTS = [
    "Violin",
    "Viola",
    "Cello",
    "Clarinet (Bb)",
    "Alto Sax (Eb)",
    "French Horn (F)",
]


# Each instrument needs two pieces of information:
# 1. Which music21 instrument class to insert into the score
# 2. Which interval is needed for transposition
INSTRUMENT_SETTINGS = {
    "Violin": {"interval": "P1", "instrument_class": instrument.Violin},
    "Viola": {"interval": "P1", "instrument_class": instrument.Viola},
    "Cello": {"interval": "P1", "instrument_class": instrument.Violoncello},
    "Clarinet (Bb)": {"interval": "M2", "instrument_class": instrument.Clarinet},
    "Alto Sax (Eb)": {"interval": "M6", "instrument_class": instrument.AltoSaxophone},
    "French Horn (F)": {"interval": "P5", "instrument_class": instrument.Horn},
}


def apply_instrument_to_part(score_part, instrument_name: str) -> None:
    """Insert the new instrument and transpose the part."""
    settings = INSTRUMENT_SETTINGS[instrument_name]
    score_part.insert(0, settings["instrument_class"]())
    score_part.transpose(interval.Interval(settings["interval"]), inPlace=True)


def mark_high_notes(score_part, highest_midi: int = 78) -> None:
    """
    Lower very high notes by one octave and color them red.

    This keeps the original beginner-friendly range check idea.
    Red notes show places a student may want to review manually.
    """
    for current_note in score_part.recurse().notes:
        if isinstance(current_note, note.Note) and current_note.pitch.midi > highest_midi:
            current_note.pitch.octave -= 1
            current_note.style.color = "red"


def create_output_path() -> str:
    """Create a temporary file path for the converted MusicXML score."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".musicxml") as temp_file:
        return temp_file.name


def transpose_score(input_file_path: str, target_instrument_name: str) -> tuple[str | None, str]:
    """
    Load a MusicXML score, transpose it for the target instrument,
    and save the converted result to a temporary file.
    """
    if target_instrument_name not in INSTRUMENT_SETTINGS:
        return None, "Unsupported instrument selected."

    try:
        score = converter.parse(input_file_path)
    except Exception as error:
        return None, f"Could not read the score file: {error}"

    try:
        for score_part in score.parts:
            apply_instrument_to_part(score_part, target_instrument_name)
            mark_high_notes(score_part)

        output_path = create_output_path()
        score.write("musicxml", fp=output_path)
        return output_path, f"Transposition complete for {target_instrument_name}."
    except Exception as error:
        return None, f"Could not transpose the score: {error}"
