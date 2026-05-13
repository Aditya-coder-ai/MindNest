"""
╔══════════════════════════════════════════════════════════════════╗
║              MindNest — AI Mood Analysis API Server              ║
║                                                                  ║
║  Flask REST API serving:                                         ║
║    • MLP Neural Network (sigmoid) for emotion classification    ║
║    • NRC VAD Lexicon for Valence-Arousal-Dominance scoring      ║
║    • Sigmoid-derived positivity scores                          ║
║    • RAG (Retrieval-Augmented Generation) knowledge retrieval   ║
║                                                                  ║
║  Emotions (10): happy, sad, angry, anxious, calm, tired,        ║
║                 grateful, lonely, excited, frustrated            ║
║                                                                  ║
║  Endpoints:                                                      ║
║    POST /api/analyze    — Analyze mood from journal text          ║
║    GET  /api/health     — Server health check                    ║
║    GET  /api/model-info — Model metadata & accuracy              ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import re
import random

import joblib
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# ─── VAD Scorer ──────────────────────────────────────────────────
from vad_scorer import compute_vad, positivity_from_vad, stress_from_vad, vad_summary
from rag_engine import RAGEngine

# ─── NLTK setup ─────────────────────────────────────────────────
import nltk
nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)
nltk.download("stopwords", quiet=True)
nltk.download("wordnet", quiet=True)

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

# ═════════════════════════════════════════════════════════════════
#  App Configuration
# ═════════════════════════════════════════════════════════════════

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from React frontend

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model", "emotion_classifier.pkl")

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mindnest.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ═════════════════════════════════════════════════════════════════
#  Database Model
# ═════════════════════════════════════════════════════════════════

class JournalEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=True)
    mood = db.Column(db.String(50), nullable=False)
    moodLabel = db.Column(db.String(50), nullable=False)
    emoji = db.Column(db.String(10), nullable=False)
    color = db.Column(db.String(20), nullable=False)
    positivity = db.Column(db.Integer, nullable=False)
    stressLevel = db.Column(db.String(50), nullable=False)
    insight = db.Column(db.Text, nullable=False)
    aiPowered = db.Column(db.Boolean, default=False)
    confidence = db.Column(db.Float, nullable=True)
    valence = db.Column(db.Float, nullable=True)
    arousal = db.Column(db.Float, nullable=True)
    dominance = db.Column(db.Float, nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': str(self.id),
            'text': self.text,
            'mood': self.mood,
            'moodLabel': self.moodLabel,
            'emoji': self.emoji,
            'color': self.color,
            'positivity': self.positivity,
            'stressLevel': self.stressLevel,
            'insight': self.insight,
            'aiPowered': self.aiPowered,
            'confidence': self.confidence,
            'valence': self.valence,
            'arousal': self.arousal,
            'dominance': self.dominance,
            'date': self.date.isoformat() + 'Z'
        }

with app.app_context():
    db.create_all()

# ═════════════════════════════════════════════════════════════════
#  Load Trained Model
# ═════════════════════════════════════════════════════════════════

print("MindNest AI Server -- Loading model...")

if not os.path.exists(MODEL_PATH):
    print("[Error] Model not found! Run 'python train_model.py' first.")
    print(f"   Expected path: {MODEL_PATH}")
    exit(1)

model_data = joblib.load(MODEL_PATH)
pipeline = model_data["pipeline"]
model_classes = model_data["classes"]
model_accuracy = model_data.get("accuracy", 0)
model_type = model_data.get("model_type", "Unknown")

print(f"[Success] Model loaded successfully!")
print(f"   Type: {model_type}")
print(f"   Classes: {model_classes}")
print(f"   Accuracy: {model_accuracy:.2%}")

# ─── RAG Engine ─────────────────────────────────────────────────
print("\nInitializing RAG Engine...")
rag_engine = RAGEngine()
print(f"   RAG Status: {'✅ Ready' if rag_engine.ready else '❌ Not available'}")

# ═════════════════════════════════════════════════════════════════
#  Text Preprocessing (same as training)
# ═════════════════════════════════════════════════════════════════

stop_words = set(stopwords.words("english"))
negation_words = {"not", "no", "nor", "neither", "never", "nobody", "nothing",
                  "nowhere", "hardly", "barely", "scarcely", "don", "don't",
                  "doesn", "doesn't", "didn", "didn't", "won", "won't",
                  "wouldn", "wouldn't", "couldn", "couldn't", "shouldn",
                  "shouldn't", "isn", "isn't", "aren", "aren't", "wasn",
                  "wasn't", "weren", "weren't", "haven", "haven't", "hasn",
                  "hasn't", "hadn", "hadn't", "can't", "cannot"}
stop_words -= negation_words
lemmatizer = WordNetLemmatizer()


def preprocess_text(text):
    """Preprocess text exactly like training: lowercase → clean → tokenize → lemmatize"""
    text = str(text).lower()
    text = re.sub(r"[^a-zA-Z\s]", "", text)
    try:
        tokens = word_tokenize(text)
    except LookupError:
        tokens = text.split()
    tokens = [t for t in tokens if t not in stop_words and len(t) > 1]
    tokens = [lemmatizer.lemmatize(t) for t in tokens]
    return " ".join(tokens)


# ═════════════════════════════════════════════════════════════════
#  Emotion Metadata (10 emotions)
# ═════════════════════════════════════════════════════════════════

MOOD_META = {
    "happy":      {"emoji": "😊", "label": "Happy",      "color": "#fbbf24", "positivityBase": 82},
    "sad":        {"emoji": "😔", "label": "Sad",        "color": "#60a5fa", "positivityBase": 25},
    "angry":      {"emoji": "😡", "label": "Angry",      "color": "#fb7185", "positivityBase": 18},
    "anxious":    {"emoji": "😰", "label": "Anxious",    "color": "#c084fc", "positivityBase": 30},
    "calm":       {"emoji": "😌", "label": "Calm",       "color": "#34d399", "positivityBase": 75},
    "tired":      {"emoji": "😴", "label": "Tired",      "color": "#94a3b8", "positivityBase": 40},
    "grateful":   {"emoji": "🙏", "label": "Grateful",   "color": "#f0abfc", "positivityBase": 88},
    "lonely":     {"emoji": "🥀", "label": "Lonely",     "color": "#7dd3fc", "positivityBase": 20},
    "excited":    {"emoji": "🎉", "label": "Excited",    "color": "#fcd34d", "positivityBase": 85},
    "frustrated": {"emoji": "😤", "label": "Frustrated", "color": "#fdba74", "positivityBase": 22},
}

STRESS_LEVELS = {
    "happy": "Low", "calm": "Low", "grateful": "Low", "excited": "Low",
    "sad": "Moderate", "tired": "Moderate", "lonely": "Moderate",
    "anxious": "High", "angry": "High", "frustrated": "High",
}

INSIGHTS = {
    "happy": [
        "Your positivity is radiating today! Keep nurturing what brings you joy.",
        "Great mood detected! Consider journaling what made you feel this way to revisit later.",
        "You're in a wonderful headspace. This is the perfect time for creative tasks!",
    ],
    "sad": [
        "It's okay to feel down sometimes. Be gentle with yourself today.",
        "Consider reaching out to a friend or doing something comforting.",
        "This feeling is temporary. Try a short walk or listening to your favorite song.",
    ],
    "angry": [
        "Take a few deep breaths. Your feelings are valid, but let's channel them wisely.",
        "Try writing down what's frustrating you — it can help process the emotion.",
        "Physical activity like a brisk walk can help release built-up tension.",
    ],
    "anxious": [
        "Try the 4-7-8 breathing technique: inhale 4s, hold 7s, exhale 8s.",
        "Ground yourself: name 5 things you see, 4 you hear, 3 you feel.",
        "You're stronger than your worries. Break tasks into smaller steps.",
    ],
    "calm": [
        "Beautiful balance today! Protect this peace — you've earned it.",
        "Your calmness is a superpower. Consider meditating to deepen it.",
        "A calm mind makes the best decisions. Well done on finding your center.",
    ],
    "tired": [
        "Rest is productive too. Consider a power nap or gentle stretching.",
        "Your body is asking for recovery. Honor that signal.",
        "Try limiting screen time before bed tonight for better sleep quality.",
    ],
    "grateful": [
        "Gratitude rewires your brain for happiness. You're doing something beautiful.",
        "Counting your blessings amplifies joy — keep this practice going!",
        "A grateful heart is a magnet for miracles. Your perspective is inspiring.",
    ],
    "lonely": [
        "Loneliness is a signal, not a sentence. Consider reaching out to someone today.",
        "You are worthy of connection. Try joining a community or group activity.",
        "Being alone is not the same as being lonely — nurture your relationship with yourself.",
    ],
    "excited": [
        "Channel this incredible energy into something creative or productive!",
        "Your excitement is contagious — share it with someone who matters to you.",
        "Savor this feeling! Write down what's making you this excited to remember it later.",
    ],
    "frustrated": [
        "Frustration often means you care deeply. Take a step back and reassess your approach.",
        "Try breaking the problem into smaller, manageable pieces.",
        "Remember: every expert was once a beginner. Progress isn't always linear.",
    ],
}

SUGGESTIONS = {
    "happy": [
        {"icon": "✨", "text": "Share your joy with someone you care about"},
        {"icon": "📝", "text": "Write down 3 things you're grateful for"},
        {"icon": "🎵", "text": "Create a feel-good playlist for days like this"},
    ],
    "sad": [
        {"icon": "🫂", "text": "Reach out to a friend or family member"},
        {"icon": "🍵", "text": "Make yourself a warm drink and rest"},
        {"icon": "🎧", "text": "Listen to comforting music or a podcast"},
    ],
    "angry": [
        {"icon": "🧘", "text": "Try 5 minutes of deep breathing exercises"},
        {"icon": "🏃", "text": "Go for a walk or do some physical activity"},
        {"icon": "📖", "text": "Write about what triggered this feeling"},
    ],
    "anxious": [
        {"icon": "🌬️", "text": "Practice box breathing: 4-4-4-4 pattern"},
        {"icon": "🌿", "text": "Step outside for fresh air and sunlight"},
        {"icon": "📋", "text": "Make a to-do list to organize your thoughts"},
    ],
    "calm": [
        {"icon": "🧘", "text": "Try a 10-minute guided meditation"},
        {"icon": "📚", "text": "Read something inspiring or creative"},
        {"icon": "🌅", "text": "Enjoy the moment — you deserve this peace"},
    ],
    "tired": [
        {"icon": "😴", "text": "Take a 20-minute power nap"},
        {"icon": "💧", "text": "Stay hydrated — drink a glass of water"},
        {"icon": "📵", "text": "Reduce screen time before sleeping tonight"},
    ],
    "grateful": [
        {"icon": "💌", "text": "Write a thank-you note to someone special"},
        {"icon": "🌟", "text": "Start a gratitude journal — list 5 blessings"},
        {"icon": "🤗", "text": "Pay it forward with a random act of kindness"},
    ],
    "lonely": [
        {"icon": "📱", "text": "Call or text someone you haven't spoken to in a while"},
        {"icon": "🏘️", "text": "Join a local community group or online forum"},
        {"icon": "🐾", "text": "Spend time with a pet or visit an animal shelter"},
    ],
    "excited": [
        {"icon": "📸", "text": "Capture this moment — take photos or journal it"},
        {"icon": "🗣️", "text": "Share the excitement with your closest people"},
        {"icon": "🎯", "text": "Channel this energy into your passion project"},
    ],
    "frustrated": [
        {"icon": "🔄", "text": "Take a 10-minute break and come back fresh"},
        {"icon": "🧩", "text": "Break the problem into smaller, solvable pieces"},
        {"icon": "💪", "text": "Remember past challenges you've already overcome"},
    ],
}


# ═════════════════════════════════════════════════════════════════
#  API Endpoints
# ═════════════════════════════════════════════════════════════════

@app.route("/api/entries", methods=["GET"])
def get_entries():
    """Fetch all journal entries from the SQLite database."""
    entries = JournalEntry.query.order_by(JournalEntry.date.desc()).all()
    return jsonify([e.to_dict() for e in entries])


@app.route("/api/entries", methods=["POST"])
def create_entry():
    """Save a new journal entry to the database."""
    data = request.json
    if not data:
        return jsonify({"error": "No JSON body provided"}), 400
        
    entry = JournalEntry(
        text=data.get('text', ''),
        mood=data.get('mood', 'calm'),
        moodLabel=data.get('moodLabel', 'Calm'),
        emoji=data.get('emoji', '😌'),
        color=data.get('color', '#34d399'),
        positivity=data.get('positivity', 50),
        stressLevel=data.get('stressLevel', 'Moderate'),
        insight=data.get('insight', ''),
        aiPowered=data.get('aiPowered', False),
        confidence=data.get('confidence'),
        valence=data.get('valence'),
        arousal=data.get('arousal'),
        dominance=data.get('dominance'),
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify(entry.to_dict()), 201

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint — verifies server and model are running."""
    return jsonify({
        "status": "healthy",
        "model_loaded": True,
        "model_type": model_type,
        "model_accuracy": round(model_accuracy * 100, 1),
        "classes": model_classes,
        "vad_enabled": True,
        "rag_enabled": rag_engine.ready,
        "rag_documents": len(rag_engine.documents),
    })


@app.route("/api/model-info", methods=["GET"])
def model_info():
    """Return metadata about the trained model."""
    arch = model_data.get("architecture", {})
    return jsonify({
        "model_type": model_type,
        "classes": model_classes,
        "accuracy": round(model_accuracy * 100, 1),
        "features": "TF-IDF (5000 max, unigrams + bigrams)",
        "preprocessing": "Lowercase → Clean → Tokenize → Remove stopwords → Lemmatize",
        "framework": "scikit-learn (MLPClassifier)",
        "activation": "Sigmoid (logistic)",
        "architecture": arch,
        "vad_scoring": "NRC VAD Lexicon + Sigmoid positivity transform",
    })


@app.route("/api/analyze", methods=["POST"])
def analyze_mood():
    """
    Main AI endpoint — analyzes journal text and returns:
    - MLP Neural Network emotion prediction (sigmoid activation)
    - NRC VAD Lexicon scores (Valence, Arousal, Dominance)
    - Sigmoid-derived positivity score
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "No JSON body provided"}), 400

    text = data.get("text", "").strip()
    selected_mood = data.get("selectedMood", None)

    # If no text, fall back to the selected mood
    if not text and not selected_mood:
        return jsonify({"error": "Provide 'text' or 'selectedMood'"}), 400

    if text:
        # ── AI Prediction (MLP with sigmoid) ──
        clean_text = preprocess_text(text)
        prediction = pipeline.predict([clean_text])[0]
        probabilities = pipeline.predict_proba([clean_text])[0]
        confidence = float(max(probabilities)) * 100

        # Build probability map
        all_probs = {}
        for cls, prob in zip(pipeline.classes_, probabilities):
            all_probs[cls] = round(float(prob) * 100, 1)

        detected = prediction

        # If user selected a mood AND the AI confidence is low, blend
        if selected_mood and confidence < 45:
            detected = selected_mood

        # ── VAD Scoring (NRC Lexicon) ──
        vad = compute_vad(text)
        vad_labels = vad_summary(vad)

        # ── Positivity via Sigmoid transform of VAD ──
        positivity = positivity_from_vad(vad)

        # ── Stress from VAD ──
        stress = stress_from_vad(vad)
    else:
        # No text — use the selected mood directly
        detected = selected_mood
        confidence = 100.0
        all_probs = {m: 0 for m in model_classes}
        all_probs[detected] = 100.0
        vad = {"valence": 0.5, "arousal": 0.5, "dominance": 0.5,
               "matched_words": 0, "total_words": 0}
        vad_labels = {"valenceLabel": "Neutral", "arousalLabel": "Moderate",
                      "dominanceLabel": "Moderate"}
        meta = MOOD_META.get(detected, MOOD_META["calm"])
        jitter = random.randint(-7, 7)
        positivity = max(5, min(98, meta["positivityBase"] + jitter))
        stress = STRESS_LEVELS.get(detected, "Moderate")

    # ── Build response ──
    meta = MOOD_META.get(detected, MOOD_META["calm"])

    insight_pool = INSIGHTS.get(detected, INSIGHTS["calm"])
    insight = random.choice(insight_pool)

    # ── RAG: Retrieve relevant context ──
    rag_context = rag_engine.get_augmented_response(
        query_text=text or "",
        detected_emotion=detected,
        top_k=2,
    )

    response = {
        "mood": detected,
        "moodLabel": meta["label"],
        "emoji": meta["emoji"],
        "color": meta["color"],
        "positivity": round(positivity),
        "stressLevel": stress,
        "insight": insight,
        "suggestions": SUGGESTIONS.get(detected, SUGGESTIONS["calm"]),
        "confidence": round(confidence, 1),
        "allProbabilities": all_probs,
        "aiPowered": True,
        # ── VAD Scores ──
        "vad": {
            "valence": vad["valence"],
            "arousal": vad["arousal"],
            "dominance": vad["dominance"],
            "matchedWords": vad["matched_words"],
            "totalWords": vad["total_words"],
            **vad_labels,
        },
        # ── RAG Context ──
        "rag": rag_context,
    }

    return jsonify(response)


@app.route("/api/rag-query", methods=["POST"])
def rag_query():
    """Direct RAG query endpoint — retrieve knowledge by topic."""
    data = request.get_json()
    if not data or not data.get("query"):
        return jsonify({"error": "Provide a 'query' field"}), 400

    query_text = data["query"]
    emotion = data.get("emotion", None)
    top_k = min(data.get("top_k", 3), 5)  # Cap at 5

    results = rag_engine.retrieve(query_text, emotion, top_k=top_k)

    return jsonify({
        "query": query_text,
        "emotion": emotion,
        "results": results,
        "totalDocuments": len(rag_engine.documents),
    })


# ═════════════════════════════════════════════════════════════════
#  Start Server
# ═════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  MindNest AI Server")
    print(f"  Model: {model_type}")
    print("  VAD Scoring: NRC Lexicon + Sigmoid")
    print(f"  RAG Engine: {'✅ Active' if rag_engine.ready else '❌ Inactive'} ({len(rag_engine.documents)} docs)")
    print("  http://localhost:5000")
    print("  CORS enabled for React frontend")
    print("=" * 50 + "\n")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
    )
