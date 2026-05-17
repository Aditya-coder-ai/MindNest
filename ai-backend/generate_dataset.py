"""
╔══════════════════════════════════════════════════════════════════╗
║   MindNest — Generate High-Quality Training Dataset             ║
║                                                                  ║
║   Creates a curated dataset of journal-style entries that        ║
║   closely match real user input. Each entry is written in        ║
║   first-person journal style, unlike Reddit comments.            ║
║                                                                  ║
║   Strategy: Template expansion with variation                    ║
║     • 60-80 unique seed sentences per emotion                    ║
║     • Mix of short + long + direct emotion words                 ║
║     • Augmented with prefixes, suffixes, and word drops          ║
║     • ~800 samples per emotion → ~8000 total                     ║
║                                                                  ║
║   Usage:   python generate_dataset.py                            ║
║   Output:  data/emotions_dataset.csv                             ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import random
import csv

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

random.seed(42)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_CSV = os.path.join(BASE_DIR, "data", "emotions_dataset.csv")

# ═════════════════════════════════════════════════════════════════
#  Seed sentences — first-person journal style
#  IMPORTANT: Each category includes SHORT, DIRECT sentences
#  containing the emotion keyword so the model learns
#  "I feel happy" → happy, "I am sad" → sad, etc.
# ═════════════════════════════════════════════════════════════════

SEEDS = {
    "happy": [
        "I feel happy today",
        "I am happy",
        "I feel so happy right now",
        "I am really happy about everything",
        "I feel very happy today",
        "I am feeling happy and great",
        "Today I feel happy",
        "I am in a happy mood today",
        "Feeling happy and positive",
        "I feel joyful and happy",
        "I am feeling great today",
        "I feel wonderful today",
        "Life is good and I am happy",
        "I feel good about myself today",
        "I am in a great mood",
        "I had such an amazing day today everything just clicked",
        "Feeling so happy right now life is beautiful",
        "I am on top of the world today nothing can bring me down",
        "Today was wonderful I spent quality time with my loved ones",
        "I feel so good about myself and my progress lately",
        "I woke up feeling grateful and happy for another beautiful day",
        "Everything is going so well I cannot stop smiling",
        "I had a great conversation with a friend and it made my day",
        "Feeling blessed and full of joy after hearing the good news",
        "I accomplished something I have been working on for weeks and I am thrilled",
        "My heart is so full of happiness today",
        "I laughed so hard today it felt so good to be carefree",
        "I received a compliment that really made me feel wonderful",
        "Today I realized how lucky I am to have such great people in my life",
        "I feel a deep sense of contentment and peace with where I am",
        "I am so proud of the progress I have made this month",
        "I surprised my friend and their reaction made me so happy",
        "I feel like everything is finally falling into place in my life",
        "I danced around my room because I was so happy about the news",
        "Today was one of the best days I have had in a long time",
    ],
    "sad": [
        "I feel sad today",
        "I am sad",
        "I feel so sad right now",
        "I am really sad about everything",
        "I feel very sad today",
        "Today I feel sad and down",
        "I am in a sad mood today",
        "Feeling sad and low",
        "I feel unhappy and sad",
        "I am feeling down today",
        "I feel miserable right now",
        "I feel so down and blue",
        "I feel terrible today",
        "Nothing makes me happy I am just sad",
        "I am feeling so low today",
        "I feel really down today nothing seems to make me feel better",
        "I have been crying all morning and I do not know why",
        "Everything feels heavy and grey I just want to stay in bed",
        "I miss someone so much it physically hurts my chest",
        "I feel so empty inside like nothing matters anymore",
        "Today was really hard I could not stop the tears from falling",
        "I feel like I have lost my spark and I do not know how to get it back",
        "I am grieving and the pain is overwhelming",
        "I feel so disappointed in how things turned out",
        "Nothing brings me joy lately everything feels flat and meaningless",
        "I keep replaying sad memories in my head and I cannot stop",
        "I feel a deep sadness that I cannot quite explain",
        "I woke up feeling heavy hearted and the feeling has not gone away",
        "I feel like crying but the tears will not come",
        "I am so heartbroken I do not know how to move forward",
        "I received some bad news and I feel crushed",
        "I feel numb and disconnected from everything around me",
        "I cannot seem to shake this feeling of hopelessness",
        "I miss the way things used to be and it makes me so sad",
        "I feel emotionally drained and deeply unhappy",
    ],
    "angry": [
        "I feel angry today",
        "I am angry",
        "I feel so angry right now",
        "I am really angry about this",
        "I feel very angry today",
        "I am mad",
        "I feel furious right now",
        "I am so mad about what happened",
        "Feeling angry and upset",
        "I am feeling rage inside me",
        "I feel irritated and angry",
        "I am fuming right now",
        "I am pissed off today",
        "I feel enraged by this situation",
        "I am boiling with anger",
        "I am so furious right now I can barely think straight",
        "Someone was incredibly rude to me today and I am still fuming",
        "I feel so much rage about how unfairly I was treated",
        "I am angry at myself for making the same mistake again",
        "I want to scream because nothing is going the way it should",
        "I am so mad about the injustice I witnessed today",
        "I feel my blood boiling when I think about what happened",
        "I cannot believe how disrespectful that person was to me",
        "I am absolutely livid about the situation at work",
        "I hate how people take advantage of my kindness",
        "I am seething with anger and I need to calm down",
        "The way I was treated today was completely unacceptable",
        "I feel like exploding because of all this pent up anger",
        "I am outraged by the unfairness of this whole situation",
        "I snapped at someone today because I could not control my anger",
    ],
    "anxious": [
        "I feel anxious today",
        "I am anxious",
        "I feel so anxious right now",
        "I am really anxious about everything",
        "I feel very nervous today",
        "I am worried about everything",
        "I feel scared and anxious",
        "I am feeling nervous",
        "Feeling anxious and stressed",
        "I feel worried and tense",
        "I am freaking out right now",
        "I feel uneasy and anxious",
        "I am so stressed out today",
        "I feel panicky and afraid",
        "I am nervous about tomorrow",
        "I cannot stop worrying about everything that could go wrong",
        "My heart is racing and I feel like something bad is about to happen",
        "I am so anxious about the exam tomorrow I cannot focus on anything",
        "I feel a constant sense of dread that I cannot shake off",
        "I am overthinking everything and driving myself crazy",
        "I feel nervous and on edge all the time lately",
        "I woke up with a knot in my stomach from all the worry",
        "I am having panic attacks and I feel out of control",
        "I am scared about the future and what it holds for me",
        "I feel tense and restless like I cannot sit still",
        "Every little thing makes me anxious and stressed these days",
        "I am afraid of failing and it is paralyzing me",
        "I feel overwhelmed by all the responsibilities on my plate",
        "My mind keeps racing with worst case scenarios",
        "I cannot sleep because my mind will not stop racing with worries",
    ],
    "calm": [
        "I feel calm today",
        "I am calm",
        "I feel so calm and peaceful",
        "I am feeling peaceful right now",
        "I feel very relaxed today",
        "I am at peace",
        "I feel serene and calm",
        "I am feeling tranquil",
        "Feeling calm and relaxed",
        "I feel centered and balanced",
        "I am in a peaceful state of mind",
        "I feel at ease with everything",
        "I am completely relaxed right now",
        "I feel still and quiet inside",
        "I am feeling very mellow today",
        "I feel completely at peace with myself and the world today",
        "I had a wonderful meditation session and I feel centered",
        "Everything feels balanced and serene right now",
        "I took a long walk in nature and I feel so refreshed and calm",
        "I feel relaxed and content just sitting quietly with my thoughts",
        "I am at ease with how things are going in my life",
        "I feel a deep inner stillness that is so comforting",
        "I spent the morning doing yoga and I feel so peaceful now",
        "I am taking things one step at a time and it feels good",
        "I feel grounded and stable nothing is bothering me today",
        "I had a quiet evening reading and I feel so serene",
        "I feel harmony between my mind and body today",
        "I feel safe and comfortable in my own skin right now",
        "I sat by the water today and let all my worries drift away",
        "I feel a gentle calmness washing over me like a warm breeze",
    ],
    "tired": [
        "I feel tired today",
        "I am tired",
        "I feel so tired right now",
        "I am really tired and exhausted",
        "I feel very tired today",
        "I am exhausted",
        "I feel sleepy and tired",
        "I am feeling drained",
        "Feeling tired and worn out",
        "I feel fatigued and exhausted",
        "I am so sleepy right now",
        "I feel wiped out today",
        "I am feeling burnt out",
        "I feel completely drained of energy",
        "I am dead tired today",
        "I am so tired today I can barely keep my eyes open",
        "I feel completely exhausted after a long day at work",
        "I need to sleep I am running on empty right now",
        "I feel drained and fatigued I just want to rest",
        "Burnout is real I have no energy left for anything",
        "I feel weary and sluggish everything feels like a chore",
        "I cannot focus anymore my brain is foggy from lack of sleep",
        "I stayed up too late last night and now I am paying for it",
        "I feel lethargic and drowsy all day long",
        "My body is aching from exhaustion I need a break",
        "I have been working nonstop and I am completely spent",
        "I just want to crawl into bed and sleep for a week",
        "I am so sleepy I keep yawning during every conversation",
        "I feel like a zombie today no amount of coffee helps",
        "I am running on fumes and desperately need some rest",
    ],
    "grateful": [
        "I feel grateful today",
        "I am grateful",
        "I feel so grateful right now",
        "I am really grateful for everything",
        "I feel very thankful today",
        "I am thankful",
        "I feel blessed and grateful",
        "I am feeling appreciative",
        "Feeling grateful and blessed",
        "I feel thankful for what I have",
        "I am so appreciative right now",
        "I feel a deep sense of gratitude",
        "I am grateful for this day",
        "I feel truly blessed today",
        "I am feeling very thankful",
        "I am so grateful for the amazing people in my life",
        "I feel blessed and thankful for everything I have",
        "I appreciate the small moments that make life beautiful",
        "I am thankful for my health and the ability to enjoy each day",
        "I feel an overwhelming sense of gratitude for my family",
        "I am grateful for the kindness that was shown to me today",
        "I realize how fortunate I am and I do not take it for granted",
        "I feel so appreciative of the love and support around me",
        "I am counting my blessings today and there are so many",
        "I am thankful for the lessons I have learned even the hard ones",
        "I feel a deep gratitude for the opportunities that have come my way",
        "I am grateful for this moment of peace and happiness",
        "I appreciate the generosity of the people who helped me",
        "I feel humbled and thankful for everything life has given me",
        "I am so grateful for my friends who always have my back",
    ],
    "lonely": [
        "I feel lonely today",
        "I am lonely",
        "I feel so lonely right now",
        "I am really lonely and isolated",
        "I feel very lonely today",
        "I am alone",
        "I feel isolated and lonely",
        "I am feeling so alone",
        "Feeling lonely and disconnected",
        "I feel abandoned and lonely",
        "I am so alone right now",
        "I feel left out and lonely",
        "I am feeling isolated today",
        "I feel like nobody cares about me",
        "I am all alone and it hurts",
        "I feel so alone even when I am surrounded by people",
        "Nobody seems to understand what I am going through",
        "I feel invisible like nobody even notices I exist",
        "I spend most of my time alone and it is getting to me",
        "I feel disconnected from everyone around me lately",
        "I wish I had someone to talk to but there is nobody there",
        "I feel isolated and cut off from the rest of the world",
        "I sit in my room alone every night wondering if anyone cares",
        "I feel like I do not belong anywhere or with anyone",
        "Nobody reaches out to me and it hurts more than I expected",
        "I feel abandoned by the people I thought cared about me",
        "I am surrounded by people but I still feel so desperately alone",
        "I feel forgotten and left out of everything going on",
        "I eat alone every day and the silence is deafening",
        "I crave human connection but I do not know how to find it",
    ],
    "excited": [
        "I feel excited today",
        "I am excited",
        "I feel so excited right now",
        "I am really excited about this",
        "I feel very excited today",
        "I am thrilled",
        "I feel pumped and excited",
        "I am feeling enthusiastic",
        "Feeling excited and energized",
        "I feel hyped up right now",
        "I am so stoked about this",
        "I feel a rush of excitement",
        "I am bursting with excitement",
        "I feel electrified and eager",
        "I am super excited right now",
        "I am so excited about the trip we planned for next month",
        "I cannot wait for the concert tonight I am buzzing with anticipation",
        "I just got the best news ever and I am over the moon excited",
        "I am thrilled about starting my new job next week",
        "I feel a rush of adrenaline thinking about the adventure ahead",
        "I am pumped up and ready to take on this amazing opportunity",
        "I am counting down the days until my birthday party",
        "I feel an incredible surge of energy and enthusiasm right now",
        "I am so stoked about the project we are working on together",
        "I cannot contain my excitement about the surprise I planned",
        "I am bursting with enthusiasm about learning this new skill",
        "I feel giddy and excited like a kid on Christmas morning",
        "I am exhilarated by the possibilities that lie ahead of me",
        "I am ecstatic about the progress I have been making lately",
        "I am fired up and motivated to make great things happen",
    ],
    "frustrated": [
        "I feel frustrated today",
        "I am frustrated",
        "I feel so frustrated right now",
        "I am really frustrated with everything",
        "I feel very frustrated today",
        "I am stuck and frustrated",
        "I feel blocked and frustrated",
        "I am feeling defeated",
        "Feeling frustrated and stuck",
        "I feel exasperated right now",
        "I am so fed up with this",
        "I feel helpless and frustrated",
        "I am at my wits end today",
        "I feel like nothing is working",
        "I am completely stuck",
        "I keep trying but nothing seems to work no matter what I do",
        "I am so frustrated with myself for not being good enough",
        "I feel stuck and unable to make any progress on my goals",
        "I hit another roadblock and I am ready to give up",
        "I am fed up with how slowly everything is moving forward",
        "I feel defeated because my efforts are not producing results",
        "I have tried everything and nothing is working I am at my limit",
        "I feel exasperated by all the setbacks I keep encountering",
        "I cannot figure this out and it is driving me absolutely crazy",
        "I am frustrated that things are not going according to plan",
        "I feel helpless because no matter what I do it is never enough",
        "I am stuck in a rut and I do not know how to get out of it",
        "I feel blocked at every turn and it is incredibly discouraging",
        "I am so aggravated by the constant obstacles in my way",
        "I keep failing and it is making me question everything",
    ],
}

# ═════════════════════════════════════════════════════════════════
#  Augmentation
# ═════════════════════════════════════════════════════════════════

PREFIXES = ["", "", "", "Honestly ", "Today ", "Right now ", "Lately ", "I think "]
SUFFIXES = ["", "", "", " honestly", " and I mean it", " today", " right now", " lately"]

# Synonym swaps for richer vocabulary
SWAPS = {
    "happy": ["joyful", "elated", "cheerful", "delighted", "pleased"],
    "sad": ["heartbroken", "miserable", "gloomy", "sorrowful", "dejected"],
    "angry": ["furious", "enraged", "livid", "mad", "irate"],
    "anxious": ["nervous", "worried", "uneasy", "stressed", "panicky"],
    "calm": ["peaceful", "serene", "tranquil", "relaxed", "mellow"],
    "tired": ["exhausted", "drained", "fatigued", "sleepy", "weary"],
    "grateful": ["thankful", "appreciative", "blessed", "fortunate", "humbled"],
    "lonely": ["alone", "isolated", "disconnected", "forsaken", "solitary"],
    "excited": ["thrilled", "ecstatic", "pumped", "hyped", "enthusiastic"],
    "frustrated": ["exasperated", "stuck", "aggravated", "defeated", "stymied"],
}

def augment(text, emotion):
    """Create a slightly varied version of a seed sentence."""
    words = text.split()
    # Randomly drop 0-1 words (not first or last)
    if len(words) > 6 and random.random() < 0.4:
        drop = random.randint(2, len(words) - 2)
        words = words[:drop] + words[drop+1:]
    
    # Synonym swap: replace the emotion keyword with a synonym 30% of the time
    if random.random() < 0.3 and emotion in SWAPS:
        synonym = random.choice(SWAPS[emotion])
        words = [synonym if w.lower() == emotion else w for w in words]
    
    # Random prefix/suffix
    p = random.choice(PREFIXES)
    s = random.choice(SUFFIXES)
    return p + " ".join(words) + s


def generate_dataset(target_per_class=800):
    """Generate the full dataset with augmentation."""
    records = []
    for emotion, seeds in SEEDS.items():
        # Add all seeds as-is
        for s in seeds:
            records.append({"text": s, "emotion": emotion})
        
        # Augment to reach target
        remaining = target_per_class - len(seeds)
        for _ in range(remaining):
            base = random.choice(seeds)
            records.append({"text": augment(base, emotion), "emotion": emotion})
    
    random.shuffle(records)
    return records


# ═════════════════════════════════════════════════════════════════
#  Main
# ═════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  🌿 MindNest — Journal-Style Dataset Generator")
    print("=" * 60)

    TARGET = 800
    records = generate_dataset(target_per_class=TARGET)
    
    # Save
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "emotion"])
        writer.writeheader()
        writer.writerows(records)
    
    # Stats
    from collections import Counter
    counts = Counter(r["emotion"] for r in records)
    
    print(f"\n  📊 Total samples: {len(records)}")
    print(f"  🏷️  Emotion classes: {len(counts)}")
    print(f"\n  Distribution:")
    for emo in sorted(counts):
        bar = "█" * (counts[emo] // 10)
        print(f"    {emo:>12s}: {counts[emo]:>4d}  {bar}")
    
    size_kb = os.path.getsize(OUTPUT_CSV) / 1024
    print(f"\n  💾 Saved to: {OUTPUT_CSV} ({size_kb:.0f} KB)")
    print(f"\n  Next step: python train_model.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
