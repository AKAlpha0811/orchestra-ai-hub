# Orchestra AI Hub

Orchestra AI Hub is a beginner-friendly Streamlit project for school orchestra students.

## What this project does

- Upload a MusicXML score file
- Choose a target instrument
- Transpose the score with `music21`
- Download the converted score

## Project structure

```text
Orchestra_AI/
├── app.py
├── transposer.py
├── requirements.txt
├── samples/
└── venv/
```

## Files

- `app.py`: Streamlit user interface
- `transposer.py`: score parsing and transposition logic
- `requirements.txt`: required Python packages
- `samples/`: place sample MusicXML files here for testing

## How to run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Supported instruments

- Violin
- Viola
- Cello
- Clarinet (Bb)
- Alto Sax (Eb)
- French Horn (F)
