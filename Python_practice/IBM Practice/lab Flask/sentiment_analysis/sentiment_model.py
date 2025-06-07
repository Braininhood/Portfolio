'''
This module provides sentiment analysis functionality using a pre-trained transformer model.
It uses the DistilBERT model specifically fine-tuned for sentiment analysis.
'''

from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
import torch
import re
import string

# Initialize the sentiment analysis pipeline (only once)
MODEL_NAME = "distilbert/distilbert-base-uncased-finetuned-sst-2-english"
sentiment_pipe = None

# Common English words for validation
COMMON_ENGLISH_WORDS = {
    'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'I',
    'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
    'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she',
    'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what',
    'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me',
    'good', 'bad', 'happy', 'sad', 'love', 'hate', 'nice', 'great', 'terrible',
    'like', 'dislike', 'amazing', 'awful', 'wonderful', 'horrible', 'excellent'
}

def initialize_model():
    '''
    Initialize the sentiment analysis model using the transformers pipeline
    '''
    global sentiment_pipe
    # Check if the model is already loaded
    if sentiment_pipe is None:
        try:
            # Load models with explicit model name to avoid warnings
            model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
            tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
            
            # Create pipeline with specific model/tokenizer
            sentiment_pipe = pipeline(
                "sentiment-analysis", 
                model=model, 
                tokenizer=tokenizer,
                device=-1  # Force CPU usage
            )
            print(f"Model {MODEL_NAME} loaded successfully")
        except Exception as e:
            print(f"Error loading model: {str(e)}")
            # Fallback to simple pipeline if there's an error
            sentiment_pipe = pipeline("sentiment-analysis")
    
    return sentiment_pipe

def is_gibberish(text):
    """
    Checks if text appears to be gibberish or random characters
    
    Args:
        text (str): The text to check
        
    Returns:
        bool: True if text looks like gibberish, False otherwise
    """
    # Clean up the text for analysis
    text = text.strip()
    
    # Immediately reject empty text
    if not text:
        return False  # Empty text handled separately
    
    # Check if input is a real English word/phrase
    words = text.lower().split()
    
    # For very short input (single word), check against common words
    if len(words) == 1 and len(text) <= 6:
        # If it's a very short input and not in common word list, it's likely gibberish
        if words[0] not in COMMON_ENGLISH_WORDS and not any(word.startswith(words[0]) for word in COMMON_ENGLISH_WORDS):
            # Additional check: single random short strings like "ewrte" that fail dictionary check
            if len(text) >= 3 and len(text) <= 6:
                consonants = sum(1 for c in text.lower() if c in 'bcdfghjklmnpqrstvwxyz')
                vowels = sum(1 for c in text.lower() if c in 'aeiou')
                
                # Nonsensical consonant-vowel patterns
                if vowels == 0 or (consonants / len(text) > 0.7):
                    return True
    
    # Check for very high ratio of special characters or punctuation
    punct_count = sum(1 for char in text if char in string.punctuation)
    if len(text) > 0 and punct_count / len(text) > 0.25:  # Lower threshold to catch more gibberish
        return True
    
    # Check for short nonsensical inputs (not real English words)
    if len(text) <= 10:
        # Dictionary of common English vowel patterns
        english_patterns = [r'[aeiou]', r'th', r'ch', r'sh', r'ing', r'ed', r'er', r'an', r'en']
        matches = 0
        for pattern in english_patterns:
            if re.search(pattern, text.lower()):
                matches += 1
        
        # If a short text has very few English patterns, it's likely gibberish
        if matches <= 1 and len(text) > 2:
            return True
    
    # Check for lack of English word patterns
    words = re.findall(r'\b[a-zA-Z]{1,}\b', text)
    if len(words) == 0 and len(text) > 3:
        return True
    
    # Check for random character strings (no vowels in words suggest gibberish)
    if len(text) > 3:
        has_vowels = bool(re.search(r'[aeiouAEIOU]', text))
        if not has_vowels:
            return True
    
    # Check for consonant clusters that are uncommon in English
    consonant_clusters = re.findall(r'[bcdfghjklmnpqrstvwxyz]{4,}', text.lower())
    if consonant_clusters:
        return True
            
    # Check for repetitive patterns that aren't natural in language
    if re.search(r'(.)\1{2,}', text):  # Same character repeated 3+ times (stricter)
        return True
    
    # Check ratio of consonants to vowels
    if len(text) > 5:
        vowels = sum(1 for char in text.lower() if char in 'aeiou')
        consonants = sum(1 for char in text.lower() if char in 'bcdfghjklmnpqrstvwxyz')
        if consonants > 0 and vowels / (consonants + vowels) < 0.2:  # English typically has higher vowel ratio
            return True
    
    # Check if input is likely just random keystrokes by checking for 
    # characters close to each other on keyboard
    keyboard_rows = [
        'qwertyuiop',
        'asdfghjkl',
        'zxcvbnm'
    ]
    
    # Check for sequential keyboard characters
    for i in range(len(text) - 2):
        substr = text[i:i+3].lower()
        for row in keyboard_rows:
            if substr[0] in row and substr[1] in row and substr[2] in row:
                positions = [row.find(char) for char in substr if char in row]
                if len(positions) == 3:
                    if abs(positions[0] - positions[1]) <= 2 and abs(positions[1] - positions[2]) <= 2:
                        return True
        
    return False

def sentiment_analyzer(text):
    '''
    Analyze the sentiment of the provided text.
    
    Args:
        text (str): The text to analyze
        
    Returns:
        dict: A dictionary containing 'label' and 'score' keys
    '''
    # Ensure the model is initialized
    model = initialize_model()
    
    # Handle empty input
    if not text or text.strip() == "":
        return {"label": "NEUTRAL", "score": 0.5}
        
    # Check if text is just gibberish or random characters
    if is_gibberish(text):
        return {"label": "INVALID INPUT", "score": 0.0}
    
    try:
        # Analyze sentiment
        result = model(text)[0]
        
        # Additional validation for very short inputs that might not have clear sentiment
        if len(text.split()) < 2 and 0.4 < result['score'] < 0.6:
            return {"label": "NEUTRAL", "score": 0.5}
            
        return result
    except Exception as e:
        print(f"Error during sentiment analysis: {str(e)}")
        # Return a fallback response
        return {"label": "ERROR", "score": 0.0} 