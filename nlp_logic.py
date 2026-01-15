from textblob import TextBlob
import re
import nltk

# Ensure necessary NLTK corpora are downloaded
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    print("Downloading necessary NLTK corpora...")
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')

def analyze_text_smartly(text):
    # --- 1. Machine Learning Sentiment Analysis (TextBlob) ---
    blob = TextBlob(text)
    sentiment = blob.sentiment.polarity # -1.0 to 1.0
    
    # Determine Tone Emoji based on ML Score
    if sentiment > 0.3:
        ai_emoji = "🎉" # Strong Positive
    elif sentiment > 0:
        ai_emoji = "😊" # Mild Positive
    elif sentiment < -0.3:
        ai_emoji = "🚨" # Strong Negative
    elif sentiment < 0:
        ai_emoji = "⚠️" # Mild Negative
    else:
        ai_emoji = "ℹ️" # Neutral

    # --- 2. Category Detection (Hybrid: ML Noun Phrases + Rules) ---
    # TextBlob can extract noun phrases, but for specific categories like "Sports",
    # simple keyword matching is still often more robust for domain-specific tasks.
    # We will keep the robust scoring system but enhance it with ML preprocessing if needed.
    
    categories_logic = {
        'Study': [r'\bexam\b', r'\btest\b', r'\bresult\b', r'\bgrade\b', r'\bclass\b', r'\blecture\b', r'\bassignment\b', r'\bstudy\b', r'\bcourse\b'],
        'Sports': [r'\bcricket\b', r'\bfootball\b', r'\bmatch\b', r'\bgame\b', r'\btournament\b', r'\bsport\b', r'\bplayer\b', r'\bteam\b'],
        'Events': [r'\bfest\b', r'\bparty\b', r'\bevent\b', r'\bceremony\b', r'\bworkshop\b', r'\bseminar\b', r'\bconference\b'],
        'General': [r'\bnotice\b', r'\bimportant\b', r'\battention\b', r'\bannouncement\b', r'\boffice\b', r'\bfee\b', r'\badmission\b']
    }

    text_lower = text.lower()
    scores = {cat: 0 for cat in categories_logic}
    
    for category, patterns in categories_logic.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                scores[category] += 1

    active_scores = {k: v for k, v in scores.items() if v > 0}
    
    if not active_scores:
        found_category = "General"
    else:
        found_category = max(active_scores, key=active_scores.get)

    # --- 3. Priority ---
    priority = "Normal"
    if scores['Urgent'] > 0 or "!" in text or text.isupper():
        priority = "High Priority"

    return found_category, priority, ai_emoji