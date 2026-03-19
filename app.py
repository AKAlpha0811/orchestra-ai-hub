import os
import tempfile

import streamlit as st

try:
    from practice_coach import analyze_practice_audio
except ImportError:
    analyze_practice_audio = None

try:
    from transposer import SUPPORTED_INSTRUMENTS, transpose_score
except ImportError:
    SUPPORTED_INSTRUMENTS = []
    transpose_score = None


st.set_page_config(page_title="Orchestra AI Hub", page_icon="🎻")


def render_home_page() -> None:
    """Show the main introduction page."""
    st.title("Orchestra AI Hub")
    st.header("Fill missing orchestra parts with smart score transposition")
    st.write(
        "Upload a MusicXML score and convert it for the instrument your school orchestra needs."
    )
    st.info("Use the sidebar to open the Smart Score Transposer.")


def save_uploaded_file(uploaded_file, default_suffix: str) -> str:
    """
    Save an uploaded file to a temporary file.

    Streamlit keeps uploads in memory, but our helper modules work more
    reliably when they receive a normal file path.
    """
    file_suffix = os.path.splitext(uploaded_file.name)[1] or default_suffix

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as temp_file:
        temp_file.write(uploaded_file.getbuffer())
        return temp_file.name


def render_transposer_page() -> None:
    """Show the score transposer interface."""
    st.title("Smart Score Transposer")
    st.write("Upload a MusicXML file and choose the instrument you want to create.")

    if transpose_score is None:
        st.error("The transposer module could not be loaded. Check transposer.py.")
        return

    uploaded_file = st.file_uploader(
        "Upload a score file",
        type=["mxl", "xml"],
        help="Supported formats: .xml and .mxl",
    )
    target_instrument = st.selectbox("Target instrument", SUPPORTED_INSTRUMENTS)

    if st.button("Transpose Score", type="primary"):
        if uploaded_file is None:
            st.warning("Please upload a MusicXML file before starting.")
            return

        temp_input_path = None
        result_file_path = None

        try:
            temp_input_path = save_uploaded_file(uploaded_file, ".xml")

            with st.spinner("Transposing the score..."):
                result_file_path, message = transpose_score(
                    temp_input_path,
                    target_instrument,
                )

            if result_file_path is None:
                st.error(message)
                return

            safe_name = target_instrument.lower().replace(" ", "_")
            safe_name = safe_name.replace("(", "").replace(")", "")
            safe_name = safe_name.replace("/", "_")

            with open(result_file_path, "rb") as result_file:
                st.success(message)
                st.download_button(
                    label="Download Transposed Score",
                    data=result_file.read(),
                    file_name=f"converted_for_{safe_name}.musicxml",
                    mime="application/vnd.recordare.musicxml+xml",
                )

        finally:
            # Delete temporary files after the app finishes using them.
            for file_path in (temp_input_path, result_file_path):
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)


def render_feedback_page() -> None:
    """Show the practice analysis page."""
    st.title("Practice Coach")
    st.write("Upload a practice recording to check tempo and rhythm stability.")

    if analyze_practice_audio is None:
        st.error("The Practice Coach module could not be loaded. Check practice_coach.py.")
        return

    uploaded_file = st.file_uploader(
        "Upload an audio file",
        type=["wav", "mp3", "webm"],
        help="Supported formats: .wav, .mp3, and .webm",
        key="practice_audio_uploader",
    )

    if uploaded_file is not None:
        st.audio(uploaded_file)

    if st.button("Analyze Practice", type="primary"):
        if uploaded_file is None:
            st.warning("Please upload an audio file before starting.")
            return

        temp_audio_path = None
        normalized_wav_path = None

        try:
            temp_audio_path = save_uploaded_file(uploaded_file, ".wav")

            with st.spinner("Analyzing tempo and rhythm..."):
                analysis = analyze_practice_audio(temp_audio_path)

            normalized_wav_path = analysis.get("normalized_wav_path")

            st.success("Analysis complete.")
            st.subheader("Practice Summary")
            st.write(f"Estimated BPM: **{analysis['estimated_bpm']}**")
            st.write(f"Beat consistency: **{analysis['consistency_label']}**")
            st.write(f"Tempo trend: **{analysis['tempo_trend']}**")

            st.subheader("Student Feedback")
            for feedback_line in analysis["feedback"]:
                st.write(f"- {feedback_line}")

            if normalized_wav_path and os.path.exists(normalized_wav_path):
                with open(normalized_wav_path, "rb") as wav_file:
                    st.download_button(
                        label="Download normalized WAV",
                        data=wav_file.read(),
                        file_name="practice_audio_normalized.wav",
                        mime="audio/wav",
                    )

        except Exception as error:
            st.error(f"Could not analyze this audio file: {error}")
        finally:
            for file_path in (temp_audio_path, normalized_wav_path):
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)


def main() -> None:
    """Run the Streamlit app."""
    st.sidebar.title("Orchestra AI Hub")
    menu = st.sidebar.radio(
        "Choose a page",
        ("Home", "Smart Score Transposer", "Practice Coach"),
    )

    if menu == "Home":
        render_home_page()
    elif menu == "Smart Score Transposer":
        render_transposer_page()
    else:
        render_feedback_page()


if __name__ == "__main__":
    main()
