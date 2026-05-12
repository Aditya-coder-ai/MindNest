"""
╔══════════════════════════════════════════════════════════════════╗
║               MindNest — AI Model Training Script               ║
║                                                                  ║
║  This script trains a machine learning pipeline for emotion      ║
║  classification from journal text entries.                       ║
║                                                                  ║
║  Pipeline:                                                       ║
║    1. Load & clean the labeled emotion dataset                   ║
║    2. Text preprocessing (tokenization, stop-word removal,       ║
║       lemmatization)                                             ║
║    3. Feature extraction using TF-IDF Vectorization              ║
║    4. Train a Logistic Regression classifier                     ║
║    5. Evaluate with accuracy, precision, recall, F1-score        ║
║    6. Save the trained model pipeline to disk                    ║
║                                                                  ║
║  Usage:   python train_model.py                                  ║
║  Output:  model/emotion_classifier.pkl                           ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import re
import sys
import warnings
import numpy as np
import pandas as pd
import joblib

# ─── Scikit-learn imports ────────────────────────────────────────
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
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
    print(f"     {emotion:>8s} : {count:3d}  {bar}")


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
#  PHASE 3: Feature Extraction & Model Architecture
# ═════════════════════════════════════════════════════════════════

print("\n🏗️  Phase 3: Building ML Pipeline")

# Split data: 80% training, 20% testing
X = df["clean_text"]
y = df["emotion"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y,  # Ensures equal class distribution in both sets
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
#   2. Logistic Regression: A classification algorithm that uses a
#      sigmoid function to predict class probabilities.
#      - "penalty='l2'" adds regularization to prevent overfitting
#      - "max_iter=1000" gives the optimizer enough steps to converge
#      - "C=1.0" controls regularization strength

pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(
        max_features=5000,       # Top 5000 most important words
        ngram_range=(1, 2),      # Unigrams + bigrams (e.g., "not happy")
        min_df=2,                # Word must appear in at least 2 documents
        max_df=0.95,             # Ignore words in >95% of documents
        sublinear_tf=True,       # Apply log normalization to TF
    )),
    ("classifier", LogisticRegression(
        penalty="l2",            # L2 regularization (Ridge)
        C=1.0,                   # Inverse regularization strength
        max_iter=1000,           # Max optimization iterations
        solver="lbfgs",          # Optimization algorithm
        random_state=42,
        class_weight="balanced", # Handle class imbalance
    )),
])

print("   Pipeline architecture:")
print("     ┌─────────────────────────────┐")
print("     │  TF-IDF Vectorizer          │")
print("     │  (Text → Feature Vectors)   │")
print("     │  • 5000 max features        │")
print("     │  • Unigrams + Bigrams       │")
print("     │  • Sublinear TF scaling     │")
print("     └──────────┬──────────────────┘")
print("                │")
print("     ┌──────────▼──────────────────┐")
print("     │  Logistic Regression        │")
print("     │  (Feature Vectors → Class)  │")
print("     │  • L2 regularization        │")
print("     │  • Balanced class weights   │")
print("     │  • Multinomial mode         │")
print("     └─────────────────────────────┘")


# ═════════════════════════════════════════════════════════════════
#  PHASE 4: Model Training
# ═════════════════════════════════════════════════════════════════

print("\n🧠 Phase 4: Training the Model...")

# Cross-validation (evaluate before final training)
print("   Running 5-fold cross-validation...")
cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring="accuracy")
print(f"   CV Accuracy: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

# Final training on full training set
print("   Training on full training set...")
pipeline.fit(X_train, y_train)
print("   ✅ Model trained successfully!")


# ═════════════════════════════════════════════════════════════════
#  PHASE 5: Evaluation
# ═════════════════════════════════════════════════════════════════

print("\n📊 Phase 5: Model Evaluation")

# Predict on test set
y_pred = pipeline.predict(X_test)

# Overall accuracy
accuracy = accuracy_score(y_test, y_pred)
print(f"\n   Overall Accuracy: {accuracy:.2%}")

# Detailed classification report
print("\n   Classification Report:")
print("   " + "-" * 56)
report = classification_report(y_test, y_pred, zero_division=0)
for line in report.split("\n"):
    print(f"   {line}")

# Confusion matrix
print("\n   Confusion Matrix:")
labels = sorted(y.unique())
cm = confusion_matrix(y_test, y_pred, labels=labels)
print(f"   {'':>10s}", end="")
for label in labels:
    print(f" {label:>8s}", end="")
print()
for i, label in enumerate(labels):
    print(f"   {label:>10s}", end="")
    for j in range(len(labels)):
        print(f" {cm[i][j]:>8d}", end="")
    print()


# ═════════════════════════════════════════════════════════════════
#  PHASE 6: Save Model
# ═════════════════════════════════════════════════════════════════

print(f"\n💾 Phase 6: Saving model to {MODEL_PATH}")

# Save the entire pipeline (vectorizer + classifier)
model_data = {
    "pipeline": pipeline,
    "classes": list(pipeline.classes_),
    "preprocessing_fn": "preprocess_text",
    "accuracy": accuracy,
    "cv_accuracy": cv_scores.mean(),
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
    "I had a great time at the party with my friends today",
    "I am worried about my future career and financial stability",
]

for text in test_texts:
    clean = preprocess_text(text)
    prediction = pipeline.predict([clean])[0]
    probabilities = pipeline.predict_proba([clean])[0]
    confidence = max(probabilities) * 100

    emoji_map = {
        "happy": "😊", "sad": "😔", "angry": "😡",
        "anxious": "😰", "calm": "😌", "tired": "😴",
    }
    emoji = emoji_map.get(prediction, "❓")

    print(f'\n   Input:  "{text}"')
    print(f"   Result: {emoji} {prediction.capitalize()} ({confidence:.1f}% confidence)")

    # Show all class probabilities
    prob_strs = []
    for cls, prob in zip(pipeline.classes_, probabilities):
        if prob > 0.05:
            prob_strs.append(f"{cls}={prob:.0%}")
    print(f"   Probs:  {', '.join(prob_strs)}")


# ═════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("  ✅ Training Complete!")
print(f"  📈 Final Accuracy: {accuracy:.2%}")
print(f"  💾 Model saved to: {MODEL_PATH}")
print("  🚀 Run 'python app.py' to start the API server")
print("=" * 60)
