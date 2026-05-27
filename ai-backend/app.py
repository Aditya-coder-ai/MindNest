"""
╔══════════════════════════════════════════════════════════════════╗
║              MindNest — AI Mood Analysis API Server              ║
║                  Production-Ready Enterprise Build                ║
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
║    POST /api/wellness-chat — Wellness assistant chat             ║
║    POST /api/rag-query  — Direct knowledge base retrieval        ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import re
import sys

# ─── UTF-8 Encoding ─────────────────────────────────────────────
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

# ─── Environment & Configuration ────────────────────────────────
from dotenv import load_dotenv
load_dotenv()

from config import get_config
from logger_config import setup_logging, get_logger
from error_handlers import handle_errors, validate_request, APIError, log_request

# ─── Core imports ───────────────────────────────────────────────
import random
import joblib
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

try:
    from google import genai
except ImportError:
    genai = None

# ─── VAD & RAG ──────────────────────────────────────────────────
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
#  App Initialization
# ═════════════════════════════════════════════════════════════════

app = Flask(__name__)
config = get_config()
app.config.from_object(config)

# Setup logging
logger = setup_logging(app)
app_logger = get_logger("app")

# Setup error handlers
handle_errors(app)
log_request(app)

# ─── CORS Configuration ──────────────────────────────────────────
CORS(
    app,
    origins=app.config['CORS_ORIGINS'],
    allow_headers=app.config['CORS_ALLOW_HEADERS'],
    expose_headers=app.config['CORS_EXPOSE_HEADERS'],
    supports_credentials=True,
)

# ─── Rate Limiting ───────────────────────────────────────────────
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=app.config['RATELIMIT_STORAGE_URL'],
)

# ─── Database ────────────────────────────────────────────────────
db = SQLAlchemy(app)
db_logger = get_logger("database")

# ─── Security Headers ───────────────────────────────────────────
@app.after_request
def set_security_headers(response):
    """Set security headers for all responses."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response

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

# ═════════════════════════════════════════════════════════════════
#  Load Trained Model
# ═════════════════════════════════════════════════════════════════

app_logger.info("Loading emotion classification model...")

MODEL_PATH = app.config['MODEL_PATH']
GEMINI_API_KEY = app.config['GEMINI_API_KEY']
GEMINI_MODEL = app.config['GEMINI_MODEL']

if not os.path.exists(MODEL_PATH):
    app_logger.error(f"Model not found at {MODEL_PATH}")
    app_logger.error("Run 'python train_model.py' first")
    raise FileNotFoundError(f"Model required: {MODEL_PATH}")

try:
    model_data = joblib.load(MODEL_PATH)
    pipeline = model_data["pipeline"]
    model_classes = model_data["classes"]
    model_accuracy = model_data.get("accuracy", 0)
    model_type = model_data.get("model_type", "Unknown")
    label_encoder = model_data.get("label_encoder", None)
    
    app_logger.info(f"✅ Model loaded successfully!")
    app_logger.info(f"   Type: {model_type}")
    app_logger.info(f"   Classes: {model_classes}")
    app_logger.info(f"   Accuracy: {model_accuracy:.2%}")
except Exception as e:
    app_logger.error(f"Failed to load model: {e}")
    raise

# ─── RAG Engine ─────────────────────────────────────────────────
app_logger.info("Initializing RAG Engine...")
try:
    rag_engine = RAGEngine()
    app_logger.info(f"✅ RAG Engine ready: {len(rag_engine.documents)} documents indexed")
except Exception as e:
    app_logger.warning(f"RAG Engine initialization failed: {e}")
    rag_engine = None

# ─── Gemini GenAI ───────────────────────────────────────────────
app_logger.info("Initializing Gemini GenAI...")
gemini_client = None
if genai and GEMINI_API_KEY:
    try:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        app_logger.info(f"✅ Gemini Status: Ready ({GEMINI_MODEL})")
    except Exception as e:
        app_logger.warning(f"Gemini initialization failed: {e}")
else:
    reason = "package missing" if not genai else "API key missing"
    app_logger.warning(f"Gemini unavailable: {reason}")

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


def contains_crisis_language(text):
    """Detect phrases that suggest immediate crisis so we can respond safely."""
    crisis_patterns = [
        r"\bkill myself\b",
        r"\bsuicide\b",
        r"\bend my life\b",
        r"\bwant to die\b",
        r"\bself[-\s]?harm\b",
        r"\bhurt myself\b",
    ]
    lowered = (text or "").lower()
    return any(re.search(pattern, lowered) for pattern in crisis_patterns)


WELLNESS_FALLBACK_RESPONSES = {
    "overwhelmed": [
        "It sounds like a lot is hitting you at once. Try picking just one small next step and give yourself permission to ignore the rest for a moment.",
        "Feeling overwhelmed can make everything seem urgent. Pause, take one slow breath, and choose the smallest thing you can do next.",
    ],
    "stressed": [
        "Stress is a sign that a lot is demanding your energy right now. Try a short reset: unclench your jaw, lower your shoulders, and breathe out slowly.",
        "You are carrying a lot. A 5-minute break, a glass of water, or a short walk can help your body come down a notch.",
    ],
    "sad": [
        "I am sorry things feel heavy right now. Be gentle with yourself and focus on one comforting thing you can do today.",
        "It is okay to feel sad. Rest, a warm drink, or reaching out to someone you trust can help you feel a little less alone.",
    ],
    "anxious": [
        "Anxiety can pull your mind into the future. Try naming one thing you can control in this moment and put your attention there.",
        "Take a slow breath in for 4, hold for 4, and breathe out for 6. You do not need to solve everything right now.",
    ],
    "lonely": [
        "Loneliness can feel really heavy. Sending one small message to someone you trust can be a meaningful first step.",
        "You deserve connection and care. Even a brief check-in with a friend, family member, or community can help.",
    ],
    "angry": [
        "Anger usually points to something important. Before reacting, give your body a minute to cool down with a few slow breaths.",
        "You are allowed to feel angry. Try stepping away briefly and putting the feeling into words before taking action.",
    ],
    "happy": [
        "I am glad to hear that. Hold onto what made today feel good and see if you can create a little more of it.",
        "That is wonderful. Savoring good moments can really strengthen your emotional resilience.",
    ],
    "sleep": [
        "Sleep struggles can make everything harder. A simple wind-down routine and less screen time before bed may help.",
        "If your mind feels busy at night, try writing down what is on your mind before bed so it is not all spinning in your head.",
    ],
    "default": [
        "Thank you for sharing that. I am here with you, and it may help to take things one small step at a time.",
        "I hear you. What you are feeling matters, and it is okay to slow down and care for yourself right now.",
    ],
}


def get_wellness_fallback_reply(text):
    lower = (text or "").lower()
    key_map = {
        "overwhelmed": ["overwhelm", "too much", "can't handle", "breaking down", "falling apart"],
        "stressed": ["stress", "pressure", "tense", "deadline", "exam", "work"],
        "sad": ["sad", "cry", "tears", "depressed", "down", "unhappy", "grief", "miss"],
        "anxious": ["anxious", "anxiety", "worried", "worry", "panic", "fear", "scared", "nervous"],
        "lonely": ["lonely", "alone", "isolated", "no one", "nobody", "no friends"],
        "angry": ["angry", "mad", "furious", "hate", "frustrated", "annoyed", "irritated"],
        "happy": ["happy", "great", "amazing", "wonderful", "good", "excited", "grateful"],
        "sleep": ["sleep", "insomnia", "tired", "rest", "exhausted", "can't sleep", "awake"],
    }

    for key, keywords in key_map.items():
        if any(keyword in lower for keyword in keywords):
            pool = WELLNESS_FALLBACK_RESPONSES[key]
            return random.choice(pool)

    return random.choice(WELLNESS_FALLBACK_RESPONSES["default"])


def generate_wellness_reply(message, history=None, user_name="Friend"):
    """Generate a supportive wellness reply using Gemini, with safe fallback."""
    if contains_crisis_language(message):
        return (
            "I am really sorry you are going through this. If you might hurt yourself or feel in immediate danger, "
            "call emergency services now or contact a crisis line right away. If you can, tell a trusted person near you "
            "what is happening and stay with them while you get support."
        ), False, "crisis-support"

    history = history or []
    clipped_history = history[-8:]
    transcript_lines = []
    for item in clipped_history:
        role = "Assistant" if item.get("role") == "assistant" else "User"
        content = (item.get("text") or "").strip()
        if content:
            transcript_lines.append(f"{role}: {content}")
    transcript = "\n".join(transcript_lines)

    if not gemini_client:
        return get_wellness_fallback_reply(message), False, "fallback"

    prompt = f"""
You are MindNest, a supportive wellness companion for {user_name}.

Instructions:
- Respond with empathy, calm language, and practical emotional support.
- Keep the response to 2-4 short sentences.
- Do not diagnose, prescribe medication, or claim to be a therapist.
- Encourage professional help only when the situation sounds serious.
- Ask at most one gentle follow-up question.
- Return plain text only, with no markdown.

Conversation so far:
{transcript or "No prior conversation."}

User's latest message:
{message}
""".strip()

    try:
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        reply = (response.text or "").strip()
        if reply:
            return reply, True, "gemini"
    except Exception as exc:
        print(f"[Wellness Chat] Gemini request failed: {exc}")

    return get_wellness_fallback_reply(message), False, "fallback"


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
    try:
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "environment": app.config['FLASK_ENV'],
            "model_loaded": True,
            "model_type": model_type,
            "model_accuracy": round(model_accuracy * 100, 1),
            "classes": list(model_classes),
            "vad_enabled": True,
            "rag_enabled": rag_engine is not None,
            "rag_documents": len(rag_engine.documents) if rag_engine else 0,
            "gemini_enabled": gemini_client is not None,
            "gemini_model": GEMINI_MODEL if gemini_client else None,
        }), 200
    except Exception as e:
        app_logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500


@app.route("/api/model-info", methods=["GET"])
def model_info():
    """Return metadata about the trained model."""
    try:
        arch = model_data.get("architecture", {})
        return jsonify({
            "model_type": model_type,
            "classes": list(model_classes),
            "accuracy": round(model_accuracy * 100, 1),
            "features": "TF-IDF (5000 max, unigrams + bigrams)",
            "preprocessing": "Lowercase → Clean → Tokenize → Remove stopwords → Lemmatize",
            "framework": "scikit-learn (MLPClassifier)",
            "activation": "Sigmoid (logistic)",
            "architecture": arch,
            "vad_scoring": "NRC VAD Lexicon + Sigmoid positivity transform",
        }), 200
    except Exception as e:
        app_logger.error(f"Model info retrieval failed: {e}")
        raise APIError("Failed to retrieve model information", 500, "MODEL_INFO_ERROR")


@app.route("/api/analyze", methods=["POST"])
@limiter.limit("30 per minute")
def analyze_mood():
    """
    Main AI endpoint — analyzes journal text and returns:
    - MLP Neural Network emotion prediction (sigmoid activation)
    - NRC VAD Lexicon scores (Valence, Arousal, Dominance)
    - Sigmoid-derived positivity score
    
    Request body:
    {
        "text": "Journal entry text...",
        "selectedMood": "happy" (optional)
    }
    """
    try:
        data = request.get_json()

        if not data:
            raise APIError("No JSON body provided", 400, "MISSING_BODY")

        text = (data.get("text") or "").strip()
        selected_mood = data.get("selectedMood")

        # If no text, fall back to the selected mood
        if not text and not selected_mood:
            raise APIError(
                "Provide either 'text' or 'selectedMood'",
                400,
                "MISSING_INPUT"
            )

        app_logger.debug(f"Analyzing mood - text length: {len(text)}, selected: {selected_mood}")

        if text:
            # ── AI Prediction (MLP with sigmoid) ──
            clean_text = preprocess_text(text)
            pred_raw = pipeline.predict([clean_text])[0]
            probabilities = pipeline.predict_proba([clean_text])[0]
            confidence = float(max(probabilities)) * 100

            # Decode prediction: label_encoder maps int→string
            if label_encoder is not None:
                prediction = label_encoder.inverse_transform([pred_raw])[0]
            else:
                prediction = str(pred_raw)  # Legacy model returns strings directly

            # Build probability map
            all_probs = {}
            for cls_idx, prob in enumerate(probabilities):
                if label_encoder is not None:
                    cls_name = label_encoder.inverse_transform([cls_idx])[0]
                else:
                    cls_name = str(pipeline.classes_[cls_idx])
                all_probs[cls_name] = round(float(prob) * 100, 1)

            detected = prediction

            # If user selected a mood AND the AI confidence is low, blend
            if selected_mood and confidence < 45:
                app_logger.debug(f"Low confidence ({confidence}%) - using selected mood: {selected_mood}")
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
        rag_context = {}
        if rag_engine:
            try:
                rag_context = rag_engine.get_augmented_response(
                    query_text=text or "",
                    detected_emotion=detected,
                    top_k=2,
                )
            except Exception as e:
                app_logger.warning(f"RAG retrieval failed: {e}")
                rag_context = {}

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

        app_logger.info(f"Analysis complete: {detected} (confidence: {confidence}%)")
        return jsonify(response), 200
        
    except Exception as e:
        app_logger.error(f"Mood analysis failed: {e}", exc_info=True)
        raise APIError(f"Failed to analyze mood: {str(e)}", 500, "ANALYSIS_ERROR")


@app.route("/api/rag-query", methods=["POST"])
@limiter.limit("20 per minute")
def rag_query():
    """Direct RAG query endpoint — retrieve knowledge by topic."""
    try:
        data = request.get_json()
        if not data or not data.get("query"):
            raise APIError(
                "Provide a 'query' field",
                400,
                "MISSING_QUERY"
            )

        if not rag_engine:
            raise APIError(
                "RAG engine not available",
                503,
                "RAG_UNAVAILABLE"
            )

        query_text = data["query"]
        emotion = data.get("emotion")
        top_k = min(data.get("top_k", 3), 5)  # Cap at 5

        app_logger.debug(f"RAG query: {query_text[:100]}")
        results = rag_engine.retrieve(query_text, emotion, top_k=top_k)

        return jsonify({
            "query": query_text,
            "emotion": emotion,
            "results": results,
            "totalDocuments": len(rag_engine.documents),
        }), 200
        
    except Exception as e:
        app_logger.error(f"RAG query failed: {e}", exc_info=True)
        raise APIError(f"RAG query failed: {str(e)}", 500, "RAG_QUERY_ERROR")


@app.route("/api/wellness-chat", methods=["POST"])
@limiter.limit("30 per minute")
def wellness_chat():
    """Gemini-backed wellness assistant chat endpoint."""
    try:
        data = request.get_json()
        if not data:
            raise APIError("No JSON body provided", 400, "MISSING_BODY")
            
        message = (data.get("message") or "").strip()
        if not message:
            raise APIError(
                "Provide a non-empty 'message' field",
                400,
                "MISSING_MESSAGE"
            )

        app_logger.debug(f"Wellness chat: {message[:100]}")
        
        reply, ai_powered, provider = generate_wellness_reply(
            message=message,
            history=data.get("history", []),
            user_name=(data.get("userName") or "Friend").strip() or "Friend",
        )

        return jsonify({
            "reply": reply,
            "aiPowered": ai_powered,
            "provider": provider,
        }), 200
        
    except Exception as e:
        app_logger.error(f"Wellness chat failed: {e}", exc_info=True)
        raise APIError(f"Wellness chat failed: {str(e)}", 500, "WELLNESS_CHAT_ERROR")


# ═════════════════════════════════════════════════════════════════
#  Start Server (Production-Ready)
# ═════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    
    app_logger.info("\n" + "=" * 60)
    app_logger.info("  🚀 MindNest AI Server — Starting")
    app_logger.info("=" * 60)
    app_logger.info(f"  Environment: {app.config['FLASK_ENV'].upper()}")
    app_logger.info(f"  Model: {model_type} (Accuracy: {model_accuracy:.2%})")
    app_logger.info(f"  VAD Scoring: NRC Lexicon (Sigmoid positivity)")
    app_logger.info(f"  RAG Engine: {'✅ Active' if rag_engine else '❌ Inactive'} ({len(rag_engine.documents) if rag_engine else 0} docs)")
    app_logger.info(f"  Gemini Chat: {'✅ Active' if gemini_client else '❌ Inactive'} ({GEMINI_MODEL if gemini_client else 'N/A'})")
    app_logger.info(f"  Rate Limiting: {'✅ Enabled' if app.config['RATELIMIT_ENABLED'] else '❌ Disabled'}")
    app_logger.info(f"  Database: {app.config['SQLALCHEMY_DATABASE_URI'].split('/')[-1]}")
    app_logger.info(f"  CORS Origins: {', '.join(app.config['CORS_ORIGINS'])}")
    app_logger.info(f"  Server: http://localhost:{port}")
    app_logger.info("=" * 60 + "\n")

    # Use Waitress (production WSGI server) by default
    try:
        from waitress import serve
        app_logger.info(f"🚀 Starting Waitress WSGI server on port {port}...")
        app_logger.info("   (Use gunicorn for production: gunicorn --config gunicorn_config.py wsgi:app)\n")
        serve(app, host="0.0.0.0", port=port, threads=4)
    except ImportError:
        app_logger.warning("⚠️  Waitress not installed — falling back to Flask dev server")
        app_logger.warning("   Install with: pip install waitress\n")
        app.run(
            host="0.0.0.0",
            port=port,
            debug=app.config['DEBUG'],
            use_reloader=False,
        )

