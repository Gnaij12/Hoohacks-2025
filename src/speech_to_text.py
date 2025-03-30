import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig, Part
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

def audio_to_text(path: str) -> str:

    PROJECT_ID = os.getenv("PROJECT_ID")
    print(PROJECT_ID)
    vertexai.init(project=PROJECT_ID, location="us-central1")

    model = GenerativeModel("gemini-1.5-flash-002")

    prompt = """
    Transcribe this audio to raw text.
    """

    with open(path, "rb") as f:
        audio_data = f.read()
    audio_file = Part.from_data(audio_data, mime_type="audio/wav")

    contents = [audio_file, prompt]

    response = model.generate_content(contents, generation_config=GenerationConfig(audio_timestamp=True))

    return response.text
    # Example response:
    # [00:00:00] Speaker A: Your devices are getting better over time...
    # [00:00:16] Speaker B: Welcome to the Made by Google podcast, ...
    # [00:01:00] Speaker A: So many features. I am a singer. ...
    # [00:01:33] Speaker B: Amazing. DeCarlos, same question to you, ...

if __name__ == "__main__":
    # Example usage
    # path = "Brian Cox explains quantum mechanics in 60 seconds - BBC News.wav"
    path = "Quantum Mechanics Explained in Ridiculously Simple Words.wav"
    # path = "gs://cloud-samples-data/generative-ai/audio/pixel.mp3"
    transcription = audio_to_text(path)
    print(transcription)