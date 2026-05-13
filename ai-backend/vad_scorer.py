"""
╔══════════════════════════════════════════════════════════════════╗
║         MindNest — VAD (Valence-Arousal-Dominance) Scorer       ║
║                                                                  ║
║  Uses NRC VAD Lexicon to compute continuous emotional            ║
║  dimensions from text. Each word maps to three scores:           ║
║    • Valence   (0→1): unhappy ← → happy                        ║
║    • Arousal   (0→1): calm    ← → excited                      ║
║    • Dominance (0→1): weak    ← → powerful                     ║
║                                                                  ║
║  Positivity is derived via sigmoid transform of valence.         ║
╚══════════════════════════════════════════════════════════════════╝
"""

import re
import math
import os
import csv

# ─── Sigmoid helper ──────────────────────────────────────────────
def sigmoid(x):
    """σ(x) = 1 / (1 + e^(-x))  — maps any value to (0, 1)"""
    return 1.0 / (1.0 + math.exp(-x))


# ═════════════════════════════════════════════════════════════════
#  NRC VAD Lexicon (curated subset of ~400 emotion-relevant words)
#  Format: word → (valence, arousal, dominance)  range 0.0–1.0
#  Source: NRC Valence, Arousal, Dominance Lexicon (Mohammad 2018)
# ═════════════════════════════════════════════════════════════════

NRC_VAD_LEXICON = {
    # ── Positive / Happy ──
    "happy": (0.96, 0.73, 0.72), "joy": (0.98, 0.82, 0.72),
    "love": (0.95, 0.72, 0.59), "wonderful": (0.95, 0.70, 0.69),
    "amazing": (0.92, 0.79, 0.68), "fantastic": (0.93, 0.75, 0.71),
    "great": (0.90, 0.62, 0.76), "good": (0.87, 0.51, 0.67),
    "beautiful": (0.92, 0.60, 0.57), "excellent": (0.93, 0.60, 0.79),
    "delighted": (0.94, 0.74, 0.63), "cheerful": (0.90, 0.67, 0.60),
    "thrilled": (0.90, 0.86, 0.60), "proud": (0.88, 0.64, 0.78),
    "celebrate": (0.89, 0.75, 0.62), "smile": (0.92, 0.55, 0.58),
    "laugh": (0.91, 0.73, 0.55), "fun": (0.93, 0.76, 0.56),
    "pleased": (0.87, 0.50, 0.65), "content": (0.85, 0.35, 0.62),
    "satisfied": (0.85, 0.39, 0.70), "positive": (0.85, 0.52, 0.70),
    "blessed": (0.90, 0.45, 0.55), "optimistic": (0.88, 0.55, 0.68),
    "energetic": (0.80, 0.82, 0.68), "vibrant": (0.82, 0.74, 0.62),
    "radiant": (0.85, 0.65, 0.60), "brilliant": (0.87, 0.62, 0.72),
    "glorious": (0.90, 0.65, 0.73), "magnificent": (0.91, 0.60, 0.72),
    "perfect": (0.89, 0.50, 0.72), "paradise": (0.93, 0.55, 0.52),

    # ── Sad ──
    "sad": (0.12, 0.40, 0.25), "unhappy": (0.10, 0.45, 0.30),
    "depressed": (0.08, 0.32, 0.18), "lonely": (0.12, 0.35, 0.20),
    "miss": (0.30, 0.50, 0.30), "cry": (0.15, 0.65, 0.22),
    "tears": (0.18, 0.60, 0.22), "heartbreak": (0.08, 0.72, 0.18),
    "gloomy": (0.15, 0.30, 0.25), "grief": (0.07, 0.62, 0.18),
    "miserable": (0.05, 0.55, 0.15), "sorrow": (0.10, 0.50, 0.20),
    "melancholy": (0.18, 0.32, 0.25), "hopeless": (0.05, 0.42, 0.10),
    "despair": (0.04, 0.58, 0.10), "painful": (0.10, 0.62, 0.22),
    "suffering": (0.08, 0.62, 0.15), "ache": (0.15, 0.50, 0.25),
    "broken": (0.10, 0.50, 0.15), "empty": (0.12, 0.25, 0.20),
    "lost": (0.18, 0.45, 0.18), "dark": (0.18, 0.42, 0.30),
    "shattered": (0.06, 0.68, 0.12), "devastated": (0.05, 0.70, 0.10),
    "mourn": (0.08, 0.48, 0.18), "weep": (0.10, 0.60, 0.18),
    "gloom": (0.12, 0.30, 0.22), "blue": (0.35, 0.30, 0.35),
    "down": (0.20, 0.30, 0.22), "hurt": (0.12, 0.58, 0.22),

    # ── Angry ──
    "angry": (0.08, 0.82, 0.55), "mad": (0.10, 0.78, 0.52),
    "furious": (0.05, 0.92, 0.60), "annoyed": (0.18, 0.62, 0.48),
    "irritated": (0.15, 0.65, 0.45), "frustrated": (0.12, 0.72, 0.35),
    "rage": (0.04, 0.95, 0.62), "hate": (0.05, 0.82, 0.50),
    "upset": (0.15, 0.65, 0.32), "outraged": (0.08, 0.85, 0.55),
    "livid": (0.05, 0.90, 0.58), "resentful": (0.10, 0.60, 0.38),
    "bitter": (0.12, 0.55, 0.40), "hostile": (0.08, 0.78, 0.55),
    "disgusted": (0.08, 0.72, 0.50), "furious": (0.05, 0.92, 0.60),
    "infuriating": (0.06, 0.85, 0.40), "maddening": (0.08, 0.80, 0.38),
    "seething": (0.06, 0.88, 0.50), "despise": (0.05, 0.78, 0.55),
    "scream": (0.12, 0.90, 0.50), "exploding": (0.08, 0.95, 0.45),

    # ── Anxious ──
    "anxious": (0.12, 0.75, 0.22), "worried": (0.15, 0.68, 0.25),
    "nervous": (0.15, 0.72, 0.22), "stressed": (0.10, 0.78, 0.25),
    "overwhelmed": (0.10, 0.80, 0.15), "panic": (0.05, 0.92, 0.12),
    "fear": (0.06, 0.82, 0.15), "tense": (0.15, 0.72, 0.30),
    "restless": (0.18, 0.68, 0.28), "uneasy": (0.15, 0.60, 0.25),
    "dread": (0.05, 0.78, 0.12), "apprehensive": (0.15, 0.58, 0.25),
    "terrified": (0.04, 0.90, 0.08), "paranoid": (0.08, 0.75, 0.15),
    "trembling": (0.10, 0.72, 0.12), "shaking": (0.12, 0.70, 0.15),
    "sweating": (0.15, 0.65, 0.20), "hyperventilate": (0.05, 0.90, 0.10),
    "overthinking": (0.12, 0.65, 0.20), "racing": (0.20, 0.80, 0.30),
    "pressure": (0.15, 0.72, 0.25), "deadline": (0.20, 0.70, 0.30),

    # ── Calm ──
    "calm": (0.80, 0.15, 0.60), "peaceful": (0.88, 0.12, 0.55),
    "relaxed": (0.85, 0.15, 0.58), "serene": (0.90, 0.10, 0.55),
    "tranquil": (0.88, 0.08, 0.52), "quiet": (0.68, 0.12, 0.45),
    "mindful": (0.80, 0.25, 0.62), "meditate": (0.82, 0.15, 0.60),
    "balanced": (0.78, 0.22, 0.65), "zen": (0.85, 0.10, 0.58),
    "soothing": (0.82, 0.15, 0.50), "rested": (0.80, 0.12, 0.55),
    "gentle": (0.82, 0.18, 0.42), "stillness": (0.75, 0.08, 0.48),
    "harmony": (0.85, 0.20, 0.58), "grounded": (0.78, 0.18, 0.65),
    "centered": (0.80, 0.18, 0.68), "ease": (0.82, 0.15, 0.55),
    "comfort": (0.85, 0.20, 0.52), "safe": (0.82, 0.15, 0.62),
    "steady": (0.72, 0.18, 0.65), "clarity": (0.80, 0.25, 0.68),

    # ── Tired ──
    "tired": (0.20, 0.18, 0.22), "exhausted": (0.10, 0.25, 0.15),
    "sleepy": (0.35, 0.12, 0.22), "drained": (0.10, 0.20, 0.12),
    "fatigue": (0.12, 0.22, 0.15), "burnout": (0.08, 0.30, 0.12),
    "weary": (0.15, 0.20, 0.18), "drowsy": (0.30, 0.10, 0.20),
    "lethargic": (0.15, 0.10, 0.15), "sluggish": (0.18, 0.12, 0.18),
    "sleep": (0.55, 0.10, 0.25), "yawning": (0.35, 0.12, 0.20),
    "nap": (0.50, 0.08, 0.25), "foggy": (0.25, 0.15, 0.20),
    "depleted": (0.10, 0.18, 0.10), "spent": (0.15, 0.15, 0.15),
    "zombie": (0.12, 0.20, 0.15), "heavy": (0.20, 0.22, 0.25),

    # ── Grateful ──
    "grateful": (0.92, 0.48, 0.55), "thankful": (0.90, 0.45, 0.52),
    "appreciate": (0.88, 0.42, 0.58), "blessing": (0.90, 0.45, 0.50),
    "gratitude": (0.92, 0.45, 0.55), "treasure": (0.88, 0.45, 0.52),
    "cherish": (0.90, 0.48, 0.50), "fortunate": (0.85, 0.42, 0.55),
    "valued": (0.85, 0.40, 0.58), "indebted": (0.55, 0.35, 0.30),
    "humbled": (0.72, 0.30, 0.35), "grace": (0.85, 0.32, 0.48),
    "kindness": (0.90, 0.38, 0.45), "generous": (0.85, 0.40, 0.52),
    "warmth": (0.85, 0.38, 0.48), "giving": (0.80, 0.42, 0.55),

    # ── Lonely ──
    "alone": (0.15, 0.30, 0.20), "isolated": (0.08, 0.35, 0.15),
    "abandoned": (0.05, 0.58, 0.08), "forgotten": (0.10, 0.35, 0.12),
    "invisible": (0.10, 0.30, 0.10), "disconnected": (0.12, 0.32, 0.18),
    "solitude": (0.40, 0.12, 0.30), "outsider": (0.12, 0.38, 0.15),
    "excluded": (0.08, 0.50, 0.10), "unwanted": (0.05, 0.52, 0.08),
    "neglected": (0.08, 0.42, 0.10), "rejected": (0.06, 0.60, 0.10),
    "distant": (0.20, 0.22, 0.25), "remote": (0.30, 0.18, 0.30),
    "silence": (0.40, 0.08, 0.35), "nobody": (0.10, 0.35, 0.12),

    # ── Excited ──
    "excited": (0.88, 0.90, 0.62), "thrilling": (0.85, 0.92, 0.58),
    "anticipation": (0.72, 0.75, 0.52), "eager": (0.80, 0.78, 0.58),
    "enthusiasm": (0.85, 0.80, 0.62), "adrenaline": (0.60, 0.95, 0.55),
    "pumped": (0.78, 0.88, 0.65), "stoked": (0.85, 0.85, 0.60),
    "buzzing": (0.75, 0.82, 0.55), "giddy": (0.82, 0.78, 0.42),
    "exhilarated": (0.88, 0.92, 0.60), "fired": (0.65, 0.85, 0.62),
    "ecstatic": (0.92, 0.90, 0.60), "supercharged": (0.78, 0.92, 0.65),
    "electrifying": (0.80, 0.95, 0.55), "passionate": (0.82, 0.82, 0.58),
    "countdown": (0.62, 0.70, 0.45), "butterflies": (0.60, 0.72, 0.35),
    "adventure": (0.82, 0.80, 0.60), "wonder": (0.85, 0.65, 0.48),

    # ── Frustrated ──
    "stuck": (0.12, 0.55, 0.15), "roadblock": (0.15, 0.58, 0.18),
    "failure": (0.08, 0.55, 0.12), "setback": (0.15, 0.52, 0.18),
    "defeated": (0.08, 0.48, 0.08), "blocked": (0.15, 0.55, 0.15),
    "stagnant": (0.15, 0.20, 0.15), "helpless": (0.06, 0.55, 0.05),
    "powerless": (0.05, 0.52, 0.05), "obstacle": (0.18, 0.55, 0.22),
    "impossible": (0.10, 0.60, 0.12), "useless": (0.05, 0.45, 0.08),
    "exasperated": (0.08, 0.75, 0.30), "aggravated": (0.10, 0.72, 0.35),
    "vexed": (0.10, 0.65, 0.32), "thwarted": (0.10, 0.58, 0.15),

    # ── General / Neutral ──
    "okay": (0.60, 0.25, 0.50), "fine": (0.65, 0.22, 0.52),
    "normal": (0.55, 0.18, 0.48), "average": (0.50, 0.18, 0.45),
    "nothing": (0.30, 0.15, 0.30), "something": (0.50, 0.30, 0.42),
    "today": (0.52, 0.30, 0.45), "life": (0.62, 0.42, 0.48),
    "work": (0.45, 0.52, 0.52), "people": (0.55, 0.42, 0.45),
    "feel": (0.50, 0.42, 0.40), "think": (0.52, 0.38, 0.55),
    "time": (0.52, 0.32, 0.42), "day": (0.55, 0.30, 0.42),
    "want": (0.55, 0.52, 0.45), "need": (0.42, 0.55, 0.38),
    "know": (0.58, 0.35, 0.60), "try": (0.55, 0.50, 0.50),
}


def _load_external_lexicon():
    """Try to load a full NRC VAD lexicon CSV if available."""
    lexicon_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data", "NRC-VAD-Lexicon.txt"
    )
    if not os.path.exists(lexicon_path):
        return {}

    ext_lexicon = {}
    try:
        with open(lexicon_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            next(reader, None)  # skip header
            for row in reader:
                if len(row) >= 4:
                    word = row[0].strip().lower()
                    v, a, d = float(row[1]), float(row[2]), float(row[3])
                    ext_lexicon[word] = (v, a, d)
        print(f"   📖 Loaded external NRC VAD lexicon: {len(ext_lexicon)} words")
    except Exception as e:
        print(f"   ⚠️  Could not load external lexicon: {e}")
    return ext_lexicon


# Merge: external lexicon (if present) is the base, curated overrides on top
_external = _load_external_lexicon()
VAD_LEXICON = {**_external, **NRC_VAD_LEXICON}
print(f"   📚 VAD Lexicon ready: {len(VAD_LEXICON)} words")


# ═════════════════════════════════════════════════════════════════
#  VAD Scoring Functions
# ═════════════════════════════════════════════════════════════════

def compute_vad(text):
    """
    Compute Valence, Arousal, Dominance scores for a text.

    Returns dict with:
      - valence (0–1): emotional positivity
      - arousal (0–1): emotional intensity
      - dominance (0–1): sense of control
      - matched_words: count of lexicon matches
      - total_words: count of input words
    """
    words = re.findall(r"[a-z]+", str(text).lower())
    if not words:
        return {"valence": 0.5, "arousal": 0.5, "dominance": 0.5,
                "matched_words": 0, "total_words": 0}

    v_scores, a_scores, d_scores = [], [], []
    for w in words:
        if w in VAD_LEXICON:
            v, a, d = VAD_LEXICON[w]
            v_scores.append(v)
            a_scores.append(a)
            d_scores.append(d)

    matched = len(v_scores)
    if matched == 0:
        return {"valence": 0.5, "arousal": 0.5, "dominance": 0.5,
                "matched_words": 0, "total_words": len(words)}

    return {
        "valence": round(sum(v_scores) / matched, 3),
        "arousal": round(sum(a_scores) / matched, 3),
        "dominance": round(sum(d_scores) / matched, 3),
        "matched_words": matched,
        "total_words": len(words),
    }


def positivity_from_vad(vad, weight_v=0.65, weight_a=0.15, weight_d=0.20):
    """
    Derive a 0–100 positivity score from VAD using sigmoid scaling.

    Formula:
      raw = weight_v * valence + weight_a * (1 - |arousal - 0.5|) + weight_d * dominance
      centered = (raw - 0.5) * 6     ← scale to sigmoid's sensitive range
      positivity = σ(centered) * 100  ← sigmoid maps to smooth 0–100

    The sigmoid curve prevents extreme scores and creates natural
    clustering around moderate values — more psychologically realistic.
    """
    v = vad["valence"]
    a = vad["arousal"]
    d = vad["dominance"]

    # Arousal contribution: moderate arousal is neutral;
    # very high or very low pulls score down slightly
    arousal_balance = 1.0 - abs(a - 0.5)

    raw = weight_v * v + weight_a * arousal_balance + weight_d * d
    centered = (raw - 0.5) * 6.0  # scale for sigmoid sensitivity
    score = sigmoid(centered) * 100.0

    return round(max(2, min(98, score)), 1)


def stress_from_vad(vad):
    """
    Estimate stress level from VAD dimensions.
    High arousal + low valence + low dominance = high stress.
    """
    v = vad["valence"]
    a = vad["arousal"]
    d = vad["dominance"]

    stress_raw = (1.0 - v) * 0.4 + a * 0.35 + (1.0 - d) * 0.25
    stress_pct = sigmoid((stress_raw - 0.5) * 5.0) * 100

    if stress_pct > 65:
        return "High"
    elif stress_pct > 35:
        return "Moderate"
    else:
        return "Low"


def vad_summary(vad):
    """Create a human-readable VAD summary string."""
    v, a, d = vad["valence"], vad["arousal"], vad["dominance"]

    v_label = "Very Positive" if v > 0.75 else "Positive" if v > 0.55 else "Neutral" if v > 0.40 else "Negative" if v > 0.20 else "Very Negative"
    a_label = "Very High" if a > 0.75 else "High" if a > 0.55 else "Moderate" if a > 0.35 else "Low" if a > 0.15 else "Very Low"
    d_label = "Very Strong" if d > 0.70 else "Strong" if d > 0.50 else "Moderate" if d > 0.30 else "Weak" if d > 0.15 else "Very Weak"

    return {
        "valenceLabel": v_label,
        "arousalLabel": a_label,
        "dominanceLabel": d_label,
    }
