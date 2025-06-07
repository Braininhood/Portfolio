"""Flask server for emotion detection"""

from flask import Flask, request, jsonify, render_template
from EmotionDetection import emotion_detector

app = Flask(__name__)

@app.route('/')
def home():
    """Render the home page."""
    return render_template('index.html')

@app.route('/emotionDetector', methods=['GET', 'POST'])
def emotion_detector_route():
    """
    Handle emotion detection for user input.
    Returns a JSON or string message based on input.
    """
    if request.method == 'POST':
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "Invalid text! Please try again."}), 400
        text_to_analyze = data['text']
    else:
        text_to_analyze = request.args.get('textToAnalyze')
        if not text_to_analyze:
            return jsonify({"error": "Invalid text! Please try again."}), 400

    emotions = emotion_detector(text_to_analyze)

    if emotions.get('dominant_emotion') is None:
        return jsonify({"error": "Invalid text! Please try again."}), 400

    response_str = (
        f"For the given statement, the system response is "
        f"'anger': {emotions['anger']}, "
        f"'disgust': {emotions['disgust']}, "
        f"'fear': {emotions['fear']}, "
        f"'joy': {emotions['joy']}, "
        f"'sadness': {emotions['sadness']}. "
        f"The dominant emotion is {emotions['dominant_emotion']}."
    )

    return response_str, 200

if __name__ == '__main__':
    app.run(host='localhost', port=5000)
