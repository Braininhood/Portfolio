''' Executing this function initiates the application of sentiment
    analysis to be executed over the Flask channel and deployed on
    localhost:5000.
'''
# Import Flask, render_template, request from the flask pramework package
from flask import Flask, render_template, request, send_from_directory
import os
import re
# Import the sentiment_analyzer function from the package created
from sentiment_model import sentiment_analyzer, initialize_model, is_gibberish

# Initiate the flask app
app = Flask(__name__)

# Pre-load the model at startup
initialize_model()

@app.route("/sentimentAnalyzer")
def sent_analyzer():
    ''' This code receives the text from the HTML interface and 
        runs sentiment analysis over it using sentiment_analysis()
        function. The output returned shows the label and its confidence 
        score for the provided text.
    '''
    try:
        text_to_analyze = request.args.get('textToAnalyze', '')
        
        # Pre-check for gibberish to provide better error message
        if is_gibberish(text_to_analyze):
            if len(text_to_analyze) <= 5:
                return "Input is too short or appears to be random characters. Please enter meaningful text."
            elif sum(1 for char in text_to_analyze if char in "!@#$%^&*()_+-=[]{}|\\;:'\",./<>?") > 2:
                return "Input contains too many special characters. Please enter regular text."
            else:
                return "The text appears to be random characters or gibberish. Please enter meaningful English text."
        
        response = sentiment_analyzer(text_to_analyze)
        label = response.get('label', 'UNKNOWN')
        score = response.get('score', 0.0)
        
        # Handle invalid input differently
        if label == "INVALID INPUT":
            return "The text appears to be random characters or gibberish. Please enter meaningful text."
        elif label == "NEUTRAL":
            return f"The sentiment of the text is NEUTRAL with a score of {score:.3f}"
        else:
            return f"The sentiment of the text is {label} with a score of {score:.3f}"
    except Exception as e:
        print(f"Error in sentiment analysis: {str(e)}")
        return f"Error analyzing sentiment: {str(e)}"

@app.route("/")
def render_index_page():
    ''' This function initiates the rendering of the main application
        page over the Flask channel
    '''
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    '''Serve the favicon'''
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == "__main__":
    ''' This functions executes the flask app and deploys it on localhost:5000
    '''
    print("Starting sentiment analysis server...")
    # Pre-load model before accepting requests
    initialize_model()
    app.run(debug=False, host="0.0.0.0", port=5000)
