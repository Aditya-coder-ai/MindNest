"""
╔══════════════════════════════════════════════════════════════════╗
║   MindNest — GoEmotions Dataset Preparation Script              ║
║                                                                  ║
║   Downloads the GoEmotions dataset (58k+ Reddit comments)       ║
║   from Google Research GitHub and maps 27 fine-grained          ║
║   emotions to MindNest's 10 emotion categories.                 ║
║                                                                  ║
║   GoEmotions (27) → MindNest (10) Mapping:                      ║
║     joy, amusement, love, pride     → happy                     ║
║     sadness, grief, disappointment  → sad                       ║
║     anger, annoyance, disgust       → angry                     ║
║     fear, nervousness               → anxious                   ║
║     relief, neutral, approval       → calm                      ║
║     remorse, embarrassment          → tired                     ║
║     gratitude, caring               → grateful                  ║
║     realization, confusion          → lonely                    ║
║     excitement, surprise, desire    → excited                   ║
║     disapproval, disappointment     → frustrated                ║
║                                                                  ║
║   Source: Kaggle / Google Research GoEmotions                    ║
║   Paper: "GoEmotions: A Dataset of Fine-Grained Emotions"       ║
║                                                                  ║
║   Usage:   python prepare_goemotions.py                          ║
║   Output:  data/emotions_dataset.csv                             ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import csv
import urllib.request
import io

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

import pandas as pd
import numpy as np

# ═════════════════════════════════════════════════════════════════
#  Configuration
# ═════════════════════════════════════════════════════════════════

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "goemotions_raw")
OUTPUT_CSV = os.path.join(DATA_DIR, "emotions_dataset.csv")

# GoEmotions raw data URLs from Google Cloud Storage
RAW_URLS = [
    "https://storage.googleapis.com/gresearch/goemotions/data/full_dataset/goemotions_1.csv",
    "https://storage.googleapis.com/gresearch/goemotions/data/full_dataset/goemotions_2.csv",
    "https://storage.googleapis.com/gresearch/goemotions/data/full_dataset/goemotions_3.csv",
]

EMOTIONS_URL = "https://raw.githubusercontent.com/google-research/google-research/master/goemotions/data/emotions.txt"

# GoEmotions 27 emotions (0-indexed as per emotions.txt)
GOEMOTIONS_LABELS = [
    "admiration", "amusement", "anger", "annoyance", "approval",
    "caring", "confusion", "curiosity", "desire", "disappointment",
    "disapproval", "disgust", "embarrassment", "excitement", "fear",
    "gratitude", "grief", "joy", "love", "nervousness",
    "optimism", "pride", "realization", "relief", "remorse",
    "sadness", "surprise", "neutral",
]

# ─── GoEmotions → MindNest 10-Emotion Mapping ───────────────────
# Improved mapping with psychologically tighter groupings.
# Key changes from v1:
#   - EXCLUDED "neutral" (55k generic comments were drowning "calm")
#   - Added more sources for under-represented categories
#   - Better psychological alignment for tired, lonely, frustrated
EMOTION_MAP = {
    # → happy: positive high-energy emotions
    "joy":        "happy",
    "amusement":  "happy",
    "love":       "happy",
    "pride":      "happy",
    "optimism":   "happy",

    # → sad: grief, loss, deep sorrow
    "sadness":        "sad",
    "grief":          "sad",
    "disappointment": "sad",
    "remorse":        "sad",

    # → angry: hostility, irritation, disgust
    "anger":      "angry",
    "annoyance":  "angry",
    "disgust":    "angry",

    # → anxious: fear, worry, nervousness
    "fear":         "anxious",
    "nervousness":  "anxious",
    "confusion":    "anxious",

    # → calm: relief, tranquil acceptance, approval
    # NOTE: "neutral" is EXCLUDED — it floods this class with generic text
    "relief":    "calm",
    "approval":  "calm",

    # → grateful: thankfulness, kindness, admiration
    "gratitude":  "grateful",
    "caring":     "grateful",
    "admiration": "grateful",

    # → lonely: social disconnection, feeling left out
    "embarrassment": "lonely",
    "realization":   "lonely",

    # → excited: high arousal positive anticipation
    "excitement": "excited",
    "surprise":   "excited",
    "desire":     "excited",
    "curiosity":  "excited",

    # → frustrated: blocked goals, disapproval
    "disapproval": "frustrated",
}

# Target samples per emotion (for balanced dataset)
TARGET_PER_EMOTION = 1500
MAX_TOTAL_SAMPLES = 20000


# ═════════════════════════════════════════════════════════════════
#  Download Functions
# ═════════════════════════════════════════════════════════════════

def download_file(url, dest_path):
    """Download a file from URL to local path."""
    print(f"   ⬇️  Downloading: {os.path.basename(dest_path)}")
    try:
        urllib.request.urlretrieve(url, dest_path)
        size_kb = os.path.getsize(dest_path) / 1024
        print(f"      ✅ {size_kb:.0f} KB downloaded")
        return True
    except Exception as e:
        print(f"      ❌ Download failed: {e}")
        return False


def download_raw_data():
    """Download all 3 GoEmotions CSV files from Google Research."""
    os.makedirs(RAW_DIR, exist_ok=True)

    downloaded = []
    for url in RAW_URLS:
        filename = url.split("/")[-1]
        dest = os.path.join(RAW_DIR, filename)

        if os.path.exists(dest):
            print(f"   ✅ Already exists: {filename}")
            downloaded.append(dest)
            continue

        if download_file(url, dest):
            downloaded.append(dest)

    return downloaded


# ═════════════════════════════════════════════════════════════════
#  Data Processing
# ═════════════════════════════════════════════════════════════════

def load_and_merge_raw(file_paths):
    """Load and merge all GoEmotions CSV parts."""
    dfs = []
    for fp in file_paths:
        df = pd.read_csv(fp)
        dfs.append(df)
        print(f"   📄 {os.path.basename(fp)}: {len(df)} rows, {len(df.columns)} columns")

    merged = pd.concat(dfs, ignore_index=True)
    print(f"\n   📊 Merged total: {len(merged)} rows")
    return merged


def extract_emotions(df):
    """
    Extract text and primary emotion from GoEmotions raw data.

    Strategy for higher quality:
    - Only use samples where EXACTLY ONE mapped emotion is active
    - This avoids noisy multi-label conflicts
    - Skip unmapped emotions entirely
    """
    print("\n🔍 Extracting emotions from raw data...")

    # The emotion columns are the 28 label names
    available_emotion_cols = [col for col in GOEMOTIONS_LABELS if col in df.columns]

    if not available_emotion_cols:
        print("   ⚠️  Emotion columns not found as named columns.")
        print(f"   Columns available: {list(df.columns[:10])}...")
        return pd.DataFrame()

    records = []
    skipped_multi = 0
    skipped_unmapped = 0

    for idx, row in df.iterrows():
        text = str(row.get("text", "")).strip()

        # Skip empty/very short texts
        if len(text) < 15:
            continue

        # Skip texts with too many [NAME] placeholders
        if text.count("[NAME]") > 2:
            continue

        # Clean up Reddit-specific formatting
        text = text.replace("[NAME]", "someone")
        text = text.replace("  ", " ").strip()

        # Find which emotions are annotated (value = 1)
        active_emotions = []
        for emo in available_emotion_cols:
            try:
                val = int(row[emo])
                if val == 1:
                    active_emotions.append(emo)
            except (ValueError, KeyError):
                continue

        if not active_emotions:
            continue

        # Map all active emotions to MindNest categories
        mapped_emotions = set()
        for emo in active_emotions:
            mapped = EMOTION_MAP.get(emo)
            if mapped:
                mapped_emotions.add(mapped)

        if not mapped_emotions:
            skipped_unmapped += 1
            continue

        # For highest quality: only use samples where all mapped emotions
        # agree on the same MindNest category
        if len(mapped_emotions) > 1:
            skipped_multi += 1
            continue

        mindnest_emotion = mapped_emotions.pop()

        records.append({
            "text": text,
            "emotion": mindnest_emotion,
        })

    result_df = pd.DataFrame(records)
    print(f"   ✅ Extracted {len(result_df)} clean single-label samples")
    print(f"   ⏭️  Skipped {skipped_multi} multi-category conflicts")
    print(f"   ⏭️  Skipped {skipped_unmapped} unmapped labels")
    return result_df


def balance_dataset(df, target_per_class=TARGET_PER_EMOTION, max_total=MAX_TOTAL_SAMPLES):
    """
    Balance the dataset by undersampling/oversampling each emotion category.
    """
    print(f"\n⚖️  Balancing dataset (target: ~{target_per_class} per class)...")

    balanced_parts = []

    for emotion in sorted(df["emotion"].unique()):
        subset = df[df["emotion"] == emotion]
        n = len(subset)

        if n >= target_per_class:
            # Undersample: take a random subset
            sampled = subset.sample(n=target_per_class, random_state=42)
        elif n >= target_per_class // 2:
            # Keep all — close enough
            sampled = subset
        else:
            # Oversample: duplicate + sample to reach target
            repeats = (target_per_class // n) + 1
            oversampled = pd.concat([subset] * repeats, ignore_index=True)
            sampled = oversampled.sample(n=min(target_per_class, len(oversampled)), random_state=42)

        balanced_parts.append(sampled)
        print(f"   {emotion:>12s}: {n:5d} raw → {len(sampled):5d} balanced")

    result = pd.concat(balanced_parts, ignore_index=True)

    # Shuffle the final dataset
    result = result.sample(frac=1, random_state=42).reset_index(drop=True)

    # Cap total if needed
    if len(result) > max_total:
        result = result.head(max_total)

    return result


# ═════════════════════════════════════════════════════════════════
#  Main Pipeline
# ═════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  🌿 MindNest — GoEmotions Dataset Preparation")
    print("     📦 Source: Google Research GoEmotions (Kaggle)")
    print("=" * 60)

    # Step 1: Download raw data
    print("\n📥 Step 1: Downloading GoEmotions raw data...")
    files = download_raw_data()

    if not files:
        print("❌ No data files downloaded. Check your internet connection.")
        sys.exit(1)

    # Step 2: Load and merge
    print("\n📂 Step 2: Loading raw CSV files...")
    raw_df = load_and_merge_raw(files)

    # Step 3: Extract emotions and map to MindNest categories
    processed_df = extract_emotions(raw_df)

    # Step 3b: Add synthetic "tired" data
    # GoEmotions has no natural tiredness/exhaustion category, so we generate
    # realistic training samples to avoid relying on poor proxy mappings.
    tired_templates = [
        "I am so tired today I can barely keep my eyes open",
        "Feeling completely exhausted after a long day at work",
        "I need to sleep I am running on empty right now",
        "So drained and fatigued I just want to rest",
        "Burnout is real I have no energy left for anything",
        "I feel weary and sluggish everything feels like a chore",
        "Cannot focus anymore my brain is foggy from lack of sleep",
        "I stayed up too late and now I am paying for it",
        "Feeling lethargic and drowsy all day long",
        "My body is aching from exhaustion I need a break",
        "I have been working nonstop and I am completely spent",
        "Just want to crawl into bed and sleep for a week",
        "So sleepy I keep yawning during every meeting",
        "I feel like a zombie today no amount of coffee helps",
        "Totally wiped out after that intense workout session",
        "Running on fumes I desperately need some rest",
        "I have not slept well in days and it is catching up",
        "Feeling heavy and slow like my body weighs a ton",
        "I am too tired to even think straight right now",
        "My energy is completely depleted I need to recharge",
        "So fatigued I can not even enjoy my favorite activities",
        "I have been pushing myself too hard and I am burnt out",
        "Every morning I wake up still feeling tired and drained",
        "Insomnia is killing me I toss and turn all night",
        "I am physically and mentally exhausted beyond words",
        "Feeling so worn out after taking care of everything today",
        "I need a vacation I am running on empty and stressed",
        "My eyes are heavy and I keep nodding off at my desk",
        "I have zero motivation because I am just too tired",
        "Another sleepless night has left me feeling terrible",
        "I crashed on the couch because I had no energy to move",
        "Overworked and under-rested that is my life right now",
        "I feel like I have been hit by a truck so exhausted",
        "Too tired to cook or clean just ordering takeout tonight",
        "My brain is mush from sleep deprivation and overwork",
        "I keep hitting snooze because getting up feels impossible",
        "All I want is a long nap and some peace and quiet",
        "I pushed through the day but I am absolutely wrecked now",
        "Feeling low energy and unmotivated just want to rest",
        "I have been grinding all week and my body is screaming for rest",
    ]

    # Create multiple paraphrased versions per template for variety
    import random
    random.seed(42)
    tired_records = []
    prefixes = ["", "Honestly ", "Ugh ", "Man ", "I swear ", "Seriously ", ""]
    suffixes = ["", " honestly", " it is rough", " I am done", " need help", " so bad", ""]
    for template in tired_templates:
        tired_records.append({"text": template, "emotion": "tired"})
        # Generate ~35 augmented versions per template to reach ~1500
        for _ in range(35):
            p = random.choice(prefixes)
            s = random.choice(suffixes)
            words = template.split()
            # Randomly drop 1-2 words for variety
            if len(words) > 6:
                drop_idx = random.randint(1, len(words) - 2)
                words = words[:drop_idx] + words[drop_idx+1:]
            tired_records.append({"text": p + " ".join(words) + s, "emotion": "tired"})

    tired_df = pd.DataFrame(tired_records)
    processed_df = pd.concat([processed_df, tired_df], ignore_index=True)
    print(f"\n   🔧 Added {len(tired_df)} synthetic 'tired' samples")

    # Show distribution before balancing
    print("\n   Distribution before balancing:")
    for emo, count in processed_df["emotion"].value_counts().items():
        bar = "█" * (count // 100)
        print(f"     {emo:>12s}: {count:5d}  {bar}")

    # Step 4: Balance the dataset
    balanced_df = balance_dataset(processed_df)

    # Step 5: Keep only the columns needed for training
    output_df = balanced_df[["text", "emotion"]].copy()

    # Step 6: Save to CSV
    print(f"\n💾 Step 5: Saving to {OUTPUT_CSV}")
    output_df.to_csv(OUTPUT_CSV, index=False)

    file_size = os.path.getsize(OUTPUT_CSV) / 1024
    print(f"   ✅ Saved! Size: {file_size:.0f} KB")

    # Final summary
    print("\n" + "=" * 60)
    print("  ✅ GoEmotions Dataset Preparation Complete!")
    print(f"  📊 Total samples: {len(output_df)}")
    print(f"  🏷️  Emotion classes: {output_df['emotion'].nunique()}")
    print(f"  📂 Output: {OUTPUT_CSV}")
    print()
    print("  Distribution:")
    for emo, count in output_df["emotion"].value_counts().sort_index().items():
        bar = "█" * (count // 20)
        print(f"     {emo:>12s}: {count:5d}  {bar}")
    print()
    print("  🔗 Source: GoEmotions (Google Research)")
    print("     Paper: 'GoEmotions: A Dataset of Fine-Grained Emotions'")
    print("     Kaggle: kaggle.com/datasets/shivamb/go-emotions-google-emotions-dataset")
    print()
    print("  Next step: python train_model.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
