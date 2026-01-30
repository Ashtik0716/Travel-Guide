from flask import Flask, jsonify, request
from google import genai
from flask_cors import CORS
from dotenv import load_dotenv
import os
import requests
import tempfile
import base64

load_dotenv()
MURF_API_KEY = os.getenv("ap2_d8e6450b-a0f3-4978-8edd-9fbf114fad81")
GEMINI_API_KEY = os.getenv("AIzaSyCdkkrLaXhA0jwiZiPuFsIwA7LF99N7Eso")

PROMPTS = {
    "Summary": """
You are a professional tourist guide.
Provide a high-level overview of "{place}" in {language}.

Focus on:
- The historical significance
- Why the place is famous
- Key architectural or cultural highlights

Keep the explanation concise, engaging, and easy to follow.
Avoid excessive details and dates.
Limit the response to around 200 words.

Respond ONLY in {language}.""",
    "Detailed": """
You are a professional tourist guide.
Provide a high-level overview of "{place}" in {language}.

Focus on:
- The historical significance
- Why the place is famous
- Key architectural or cultural highlights

Keep the explanation concise, engaging, and easy to follow.
Avoid excessive details and dates.
Limit the response to around 200 words.

Respond ONLY in {language}.
"""
}
app = Flask(__name__)
CORS(app)


def generate_speech(text, voice_id, locale):
    temp_audio = tempfile.NamedTemporaryFile(
        suffix=".mp3",
        delete=False
    )
    url = "https://global.api.murf.ai/v1/speech/stream"
    headers = {
        "api-key": MURF_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "voice_id": voice_id,
        "text": text,
        "multi_native_locale": locale,
        "model": "FALCON",
        "format": "MP3",
        "sampleRate": 24000,
        "channelType": "MONO"
    }

    response = requests.post(
        url,
        headers=headers,
        json=data
    )
    if response.status_code == 200:
        with open(temp_audio.name, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
    else:
        print(f"Error: {response.status_code}")

    return temp_audio

client = genai.Client(api_key=GEMINI_API_KEY)

def generate_description(place, answer_type, language):
    prompt = PROMPTS[answer_type].format(place=place, language=language)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text





@app.route('/generate-audio-guide', methods = ['POST'])
def generate_audio_guide():
    data=request.json
    print("Data: ",data)
    place = data["place"]
    answer_type = data["answerType"]
    language = data["language"]
    voice_id = "en-US-terrell"
    locale = "en-US"

    text_description = generate_description(place, answer_type, language)
    audio_path = generate_speech(text_description,voice_id,locale)

    audio_bytes = open(audio_path.name, "rb").read()
    encoded_audio = base64.b64encode(audio_bytes).decode("utf-8")
    return jsonify({
        "description": text_description,
        "audioBase64": encoded_audio
    })

 
app.run(debug=True)