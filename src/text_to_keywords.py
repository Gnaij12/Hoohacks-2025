import vertexai
from vertexai.generative_models import GenerativeModel
import os
from dotenv import load_dotenv
import json
from speech_to_text import audio_to_text
import re

load_dotenv(dotenv_path=".env")

def text_to_keywords(text: str) -> dict[str, str]:
    PROJECT_ID = os.getenv("PROJECT_ID")
    vertexai.init(project=PROJECT_ID, location="us-central1")
    model = GenerativeModel("gemini-2.0-flash-001")
    prompt = ("""Turn this transcript below surrounded by {} into only a JSON dictionary with no other words, 
        containing pairs with the keyword and the definition of that keyword in the format of {term1: definition1, term2: definition2} 
        with the terms and definitions being strings, please provide at least 4 (but as many as you can, the more the better) 
        of these term:definition pairs"""
        + "{"
        + text
        + "}"
    )
    response = model.generate_content(
        contents=prompt
    )
    # print(response.text)
    try:
        # Attempt to parse the response as JSON
        return json.loads(response.text)
    except json.JSONDecodeError:
        # If parsing fails, clean the response and try again
        # print("Failed to parse JSON. Cleaning response...")
        # Extract JSON using regex
        match = re.search(r"\{.*\}", response.text, re.DOTALL)
        if match:
            cleaned_text = match.group(0)
            try:
                return json.loads(cleaned_text)
            except json.JSONDecodeError as e:
                print("Error parsing cleaned JSON:", e)
        else:
            print("No valid JSON found in response.")
        return {}

    # return json.loads(response.text)

if __name__ == "__main__":
    # Example usage
    # path = "Brian Cox explains quantum mechanics in 60 seconds - BBC News.wav"
    path = "Quantum Mechanics Explained in Ridiculously Simple Words.wav"
    # path = "gs://cloud-samples-data/generative-ai/audio/pixel.mp3"
    text = audio_to_text(path)
    keyword_def = text_to_keywords(text)
    print(keyword_def)