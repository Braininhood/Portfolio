import requests
import json

def emotion_detector(text_to_analyze):
    url = 'https://sn-watson-emotion.labs.skills.network/v1/watson.runtime.nlp.v1/NlpService/EmotionPredict'
    headers = {"grpc-metadata-mm-model-id": "emotion_aggregated-workflow_lang_en_stock"}
    payload = {"raw_document": {"text": text_to_analyze}}

    try:
        response = requests.post(url, headers=headers, json=payload)
    except Exception as e:
        # Network or request error
        return {
            'anger': None,
            'disgust': None,
            'fear': None,
            'joy': None,
            'sadness': None,
            'dominant_emotion': None
        }

    if response.status_code == 400:
        # Bad request likely due to blank text
        return {
            'anger': None,
            'disgust': None,
            'fear': None,
            'joy': None,
            'sadness': None,
            'dominant_emotion': None
        }

    try:
        response_json = response.json()
    except Exception:
        # JSON parse error
        return {
            'anger': None,
            'disgust': None,
            'fear': None,
            'joy': None,
            'sadness': None,
            'dominant_emotion': None
        }

    # Check if 'text' key is present
    if 'text' not in response_json or response_json['text'] is None:
        return {
            'anger': None,
            'disgust': None,
            'fear': None,
            'joy': None,
            'sadness': None,
            'dominant_emotion': None
        }

    try:
        emotions_dict = json.loads(response_json['text'])
    except Exception:
        return {
            'anger': None,
            'disgust': None,
            'fear': None,
            'joy': None,
            'sadness': None,
            'dominant_emotion': None
        }

    anger = emotions_dict.get('anger', 0)
    disgust = emotions_dict.get('disgust', 0)
    fear = emotions_dict.get('fear', 0)
    joy = emotions_dict.get('joy', 0)
    sadness = emotions_dict.get('sadness', 0)

    emotions = {
        'anger': anger,
        'disgust': disgust,
        'fear': fear,
        'joy': joy,
        'sadness': sadness
    }

    dominant_emotion = max(emotions, key=emotions.get) if emotions else None

    return {
        **emotions,
        'dominant_emotion': dominant_emotion
    }
