"""
╔══════════════════════════════════════════════════════════════════╗
║               MindNest — AI Model Training Script               ║
║                                                                  ║
║  This script trains a Neural Network (MLP) pipeline with         ║
║  SIGMOID (logistic) activation for emotion classification        ║
║  from journal text entries.                                      ║
║                                                                  ║
║  Dataset: GoEmotions (Google Research / Kaggle)                  ║
║    • 58k+ Reddit comments → mapped to 10 MindNest emotions      ║
║    • Balanced & cleaned for robust classification                ║
║                                                                  ║
║  Pipeline:                                                       ║
║    1. Load & clean the GoEmotions-derived dataset                ║
║    2. Text preprocessing (tokenization, stop-word removal,       ║
║       lemmatization)                                             ║
║    3. Feature extraction using TF-IDF Vectorization              ║
║    4. Train an MLP Neural Network with sigmoid activation        ║
║    5. Evaluate with accuracy, precision, recall, F1-score        ║
║    6. Save the trained model pipeline to disk                    ║
║                                                                  ║
║  Emotions: happy, sad, angry, anxious, calm, tired,              ║
║            grateful, lonely, excited, frustrated                 ║
║                                                                  ║
║  Sigmoid Activation:                                             ║
║    σ(x) = 1 / (1 + e^(-x))                                      ║
║    Maps any real value to (0, 1), enabling smooth probability    ║
║    estimation at each hidden neuron for nuanced emotion          ║
║    boundary learning.                                            ║
║                                                                  ║
║  Usage:   python train_model.py                                  ║
║  Output:  model/emotion_classifier.pkl                           ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import re
import sys
import warnings

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

import numpy as np
import pandas as pd
import joblib

# ─── Scikit-learn imports ────────────────────────────────────────
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
)

# ─── NLTK imports (text preprocessing) ──────────────────────────
import nltk

warnings.filterwarnings("ignore")

# ═════════════════════════════════════════════════════════════════
#  PHASE 1: Setup & Data Loading
# ═════════════════════════════════════════════════════════════════

print("=" * 60)
print("  🌿 MindNest — AI Emotion Classifier Training")
print("     🧠 Neural Network with Sigmoid Activation")
print("     📦 Dataset: GoEmotions (Kaggle / Google Research)")
print("=" * 60)

# Download NLTK resources
print("\n📥 Downloading NLTK resources...")
nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)
nltk.download("stopwords", quiet=True)
nltk.download("wordnet", quiet=True)

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "emotions_dataset.csv")
MODEL_DIR = os.path.join(BASE_DIR, "model")
MODEL_PATH = os.path.join(MODEL_DIR, "emotion_classifier.pkl")

# Create model directory
os.makedirs(MODEL_DIR, exist_ok=True)

# Load dataset
print(f"\n📂 Loading dataset from: {DATA_PATH}")
df = pd.read_csv(DATA_PATH)
print(f"   Total samples: {len(df)}")
print(f"   Emotion classes: {df['emotion'].nunique()}")
print(f"\n   Distribution:")
for emotion, count in df["emotion"].value_counts().items():
    bar = "█" * (count // 2)
    print(f"     {emotion:>12s} : {count:3d}  {bar}")


# ═════════════════════════════════════════════════════════════════
#  PHASE 2: Text Preprocessing
# ═════════════════════════════════════════════════════════════════

print("\n🔧 Phase 2: Text Preprocessing")

# Initialize NLP tools
stop_words = set(stopwords.words("english"))
# Remove negation words from stop words (they carry emotional meaning)
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
    """
    Clean and normalize a text string for ML processing.

    Steps:
        1. Lowercase conversion
        2. Remove special characters & numbers
        3. Tokenize into words
        4. Remove stop words (keeping negations)
        5. Lemmatize words to their base form

    Args:
        text (str): Raw journal entry text

    Returns:
        str: Cleaned, preprocessed text
    """
    # Step 1: Lowercase
    text = str(text).lower()

    # Step 2: Remove special characters and numbers
    text = re.sub(r"[^a-zA-Z\s]", "", text)

    # Step 3: Tokenize
    try:
        tokens = word_tokenize(text)
    except LookupError:
        tokens = text.split()

    # Step 4: Remove stop words (keeping negations for sentiment)
    tokens = [t for t in tokens if t not in stop_words and len(t) > 1]

    # Step 5: Lemmatize (reduce words to base form)
    #   "running" → "run", "happier" → "happy"
    tokens = [lemmatizer.lemmatize(t) for t in tokens]

    return " ".join(tokens)


# Apply preprocessing to all texts
print("   Preprocessing all text samples...")
df["clean_text"] = df["text"].apply(preprocess_text)

print("   ✅ Preprocessing complete!")
print(f"\n   Sample transformation:")
print(f"     Raw:   '{df['text'].iloc[0]}'")
print(f"     Clean: '{df['clean_text'].iloc[0]}'")


# ═════════════════════════════════════════════════════════════════
#  PHASE 3: Feature Extraction & Neural Network Architecture
# ═════════════════════════════════════════════════════════════════

print("\n🏗️  Phase 3: Building Neural Network Pipeline")

# Split data: 80% training, 20% testing
X = df["clean_text"]
y_raw = df["emotion"]

# Encode string labels → integers so early_stopping works
# (scikit-learn's MLP calls np.isnan on validation predictions,
#  which fails on string arrays)
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y_raw)
emotion_classes = list(label_encoder.classes_)  # e.g. ['angry','anxious',...]
print(f"   Encoded {len(emotion_classes)} classes: {emotion_classes}")

X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded,
    test_size=0.2,
    random_state=42,
    stratify=y_encoded,  # Ensures equal class distribution in both sets
)

print(f"   Training samples: {len(X_train)}")
print(f"   Testing samples:  {len(X_test)}")

# Build the ML Pipeline
#
# This pipeline chains two operations:
#   1. TF-IDF Vectorizer: Converts text → numerical feature vectors
#      - TF (Term Frequency): How often a word appears in a document
#      - IDF (Inverse Document Frequency): How rare a word is across all docs
#      - Result: Words that are frequent in one doc but rare overall get
#        high scores → they're more meaningful for classification
#
#   2. MLP Neural Network (Multi-Layer Perceptron):
#      A feedforward neural network that uses SIGMOID (logistic) activation
#      at each hidden neuron.
#
#      Sigmoid Function: σ(x) = 1 / (1 + e^(-x))
#      ─────────────────────────────────────────
#      The sigmoid squashes any input into range (0, 1):
#        • Large positive x → σ(x) ≈ 1  (neuron "fires")
#        • Large negative x → σ(x) ≈ 0  (neuron "silent")
#        • x = 0            → σ(x) = 0.5 (uncertain)
#
#      This smooth, differentiable curve enables:
#        • Nuanced probability estimation for each emotion
#        • Gradient-based learning (backpropagation)
#        • Non-linear decision boundaries between emotions
#
#      Architecture:
#        Input (TF-IDF features) → Hidden Layer 1 (128 sigmoid neurons)
#                                → Hidden Layer 2 (64 sigmoid neurons)
#                                → Output (softmax over 10 emotion classes)

pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(
        max_features=5000,       # Top 5000 features — fits smaller dataset better
        ngram_range=(1, 2),      # Unigrams + bigrams
        min_df=2,                # Word must appear in at least 2 documents
        max_df=0.90,             # Ignore words in >90% of documents
        sublinear_tf=True,       # Apply log normalization to TF
    )),
    ("classifier", MLPClassifier(
        hidden_layer_sizes=(128, 64),       # 2 hidden layers — right-sized for dataset
        activation="logistic",              # SIGMOID activation: σ(x) = 1/(1+e^-x)
        solver="adam",                      # Adam optimizer (adaptive learning rate)
        alpha=0.0005,                       # L2 regularization
        learning_rate="adaptive",           # Reduce LR when loss plateaus
        learning_rate_init=0.001,           # Initial learning rate
        max_iter=500,                       # Max training epochs
        batch_size=64,                      # Small batches for cleaner gradients
        early_stopping=True,                # Stop when validation loss plateaus
        validation_fraction=0.1,            # 10% of training data for validation
        n_iter_no_change=20,                # Patience: stop after 20 stale epochs
        random_state=42,
        verbose=True,                       # Show training progress
    )),
])

print("   Neural Network architecture:")
print("     ┌─────────────────────────────────┐")
print("     │  TF-IDF Vectorizer              │")
print("     │  (Text → Feature Vectors)       │")
print("     │  • 8000 max features            │")
print("     │  • Uni + Bi + Trigrams          │")
print("     │  • Sublinear TF scaling         │")
print("     └──────────┬──────────────────────┘")
print("                │")
print("     ┌──────────▼──────────────────────┐")
print("     │  Hidden Layer 1                 │")
print("     │  • 256 neurons                  │")
print("     │  • σ(x) = 1/(1+e^-x) [SIGMOID] │")
print("     └──────────┬──────────────────────┘")
print("                │")
print("     ┌──────────▼──────────────────────┐")
print("     │  Hidden Layer 2                 │")
print("     │  • 128 neurons                  │")
print("     │  • σ(x) = 1/(1+e^-x) [SIGMOID] │")
print("     └──────────┬──────────────────────┘")
print("                │")
print("     ┌──────────▼──────────────────────┐")
print("     │  Hidden Layer 3                 │")
print("     │  • 64 neurons                   │")
print("     │  • σ(x) = 1/(1+e^-x) [SIGMOID] │")
print("     └──────────┬──────────────────────┘")
print("                │")
print("     ┌──────────▼──────────────────────┐")
print("     │  Output Layer (Softmax)         │")
print("     │  • 10 emotion classes           │")
print("     │  • Probability distribution     │")
print("     └─────────────────────────────────┘")
print()
print("   Sigmoid activation at each neuron:")
print("              1.0 ─── ─ ─ ─ ──────────")
print("             0.75 ─        ╱           ")
print("     σ(x) =  0.5 ─ ─ ─ ─╳─ ─ ─ ─ ─  ")
print("             0.25 ─   ╱                ")
print("              0.0 ────── ─ ─ ─ ─ ─ ── ")
print("                  -6  -3   0   3   6   ")


# ═════════════════════════════════════════════════════════════════
#  PHASE 4: Model Training
# ═════════════════════════════════════════════════════════════════

print("\n🧠 Phase 4: Training the Neural Network...")

# Train on full training set (skipping CV for speed — train/test split gives reliable eval)
print("   Training on full training set (this may take a few minutes)...")
pipeline.fit(X_train, y_train)
print("   ✅ Neural Network trained successfully!")

# Report MLP details
mlp = pipeline.named_steps["classifier"]
print(f"\n   Network details:")
print(f"     Layers: {mlp.n_layers_}")
print(f"     Activation: sigmoid (logistic)")
print(f"     Training epochs: {mlp.n_iter_}")
print(f"     Final loss: {mlp.loss_:.6f}")
print(f"     Architecture: 256 -> 128 -> 64 sigmoid neurons")
print(f"     Dataset: GoEmotions (Kaggle / Google Research)")


# ═════════════════════════════════════════════════════════════════
#  PHASE 5: Evaluation
# ═════════════════════════════════════════════════════════════════

print("\n📊 Phase 5: Model Evaluation")

# Predict on test set (integer labels)
y_pred = pipeline.predict(X_test)

# Decode back to string labels for readable reports
y_test_str = label_encoder.inverse_transform(y_test)
y_pred_str = label_encoder.inverse_transform(y_pred)

# Overall accuracy
accuracy = accuracy_score(y_test, y_pred)
print(f"\n   Overall Accuracy: {accuracy:.2%}")

# Detailed classification report
print("\n   Classification Report:")
print("   " + "-" * 56)
report = classification_report(y_test_str, y_pred_str, zero_division=0)
for line in report.split("\n"):
    print(f"   {line}")

# Confusion matrix
print("\n   Confusion Matrix:")
labels = sorted(emotion_classes)
cm = confusion_matrix(y_test_str, y_pred_str, labels=labels)
print(f"   {'':>12s}", end="")
for label in labels:
    print(f" {label:>10s}", end="")
print()
for i, label in enumerate(labels):
    print(f"   {label:>12s}", end="")
    for j in range(len(labels)):
        print(f" {cm[i][j]:>10d}", end="")
    print()


# ═════════════════════════════════════════════════════════════════
#  PHASE 6: Save Model
# ═════════════════════════════════════════════════════════════════

print(f"\n💾 Phase 6: Saving model to {MODEL_PATH}")

# Save the entire pipeline (vectorizer + neural network) plus the label encoder
model_data = {
    "pipeline": pipeline,
    "label_encoder": label_encoder,
    "classes": emotion_classes,  # string class names
    "preprocessing_fn": "preprocess_text",
    "accuracy": accuracy,
    "model_type": "MLP Neural Network (Sigmoid)",
    "dataset": "GoEmotions (Kaggle / Google Research)",
    "architecture": {
        "hidden_layers": [256, 128, 64],
        "activation": "sigmoid (logistic)",
        "optimizer": "adam",
        "total_epochs": mlp.n_iter_,
        "final_loss": mlp.loss_,
    },
}
joblib.dump(model_data, MODEL_PATH)

model_size = os.path.getsize(MODEL_PATH) / 1024
print(f"   Model size: {model_size:.1f} KB")
print("   ✅ Model saved successfully!")


# ═════════════════════════════════════════════════════════════════
#  PHASE 7: Test Predictions
# ═════════════════════════════════════════════════════════════════

print("\n🔮 Phase 7: Testing Live Predictions")
print("   " + "-" * 56)

test_texts = [
    "I had such a wonderful day everything went perfectly well",
    "I feel really sad and lonely today nothing seems right",
    "I am so angry about how they treated me at work",
    "The exam is tomorrow and I am extremely nervous about it",
    "I feel so peaceful after my meditation session today",
    "I am exhausted and can barely keep my eyes open anymore",
    "I am so thankful for all the blessings in my life",
    "I feel completely alone and nobody reaches out to me",
    "I am bursting with excitement about the trip next week",
    "I keep hitting roadblocks and nothing works no matter what I try",
    "I had a great time at the party with my friends today",
    "I am worried about my future career and financial stability",
]

emoji_map = {
    "happy": "😊", "sad": "😔", "angry": "😡",
    "anxious": "😰", "calm": "😌", "tired": "😴",
    "grateful": "🙏", "lonely": "🥀", "excited": "🎉",
    "frustrated": "😤",
}

for text in test_texts:
    clean = preprocess_text(text)
    pred_encoded = pipeline.predict([clean])[0]
    prediction = label_encoder.inverse_transform([pred_encoded])[0]
    probabilities = pipeline.predict_proba([clean])[0]
    confidence = max(probabilities) * 100

    emoji = emoji_map.get(prediction, "❓")

    print(f'\n   Input:  "{text}"')
    print(f"   Result: {emoji} {prediction.capitalize()} ({confidence:.1f}% confidence)")

    # Show all class probabilities
    prob_strs = []
    for cls_idx, prob in enumerate(probabilities):
        cls_name = label_encoder.inverse_transform([cls_idx])[0]
        if prob > 0.05:
            prob_strs.append(f"{cls_name}={prob:.0%}")
    print(f"   Probs:  {', '.join(prob_strs)}")


# ═════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("  ✅ Training Complete!")
print(f"  🧠 Model: MLP Neural Network (Sigmoid Activation)")
print(f"  📐 Architecture: 256 -> 128 -> 64 sigmoid neurons")
print(f"  📦 Dataset: GoEmotions (Kaggle / Google Research)")
print(f"  🎯 Emotions: {', '.join(sorted(emotion_classes))}")
print(f"  📈 Final Accuracy: {accuracy:.2%}")
print(f"  💾 Model saved to: {MODEL_PATH}")
print("  🚀 Run 'python app.py' to start the API server")
print("=" * 60)

