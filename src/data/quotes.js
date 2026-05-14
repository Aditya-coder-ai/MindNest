/* ===================================================================
   MindNest — Curated Daily Quotes
   Mindfulness, wellness, meditation, self-care & calming affirmations
   =================================================================== */

const DAILY_QUOTES = [
  // Mindfulness
  { text: "The present moment is filled with joy and happiness. If you are attentive, you will see it.", author: "Thich Nhat Hanh", category: "mindfulness" },
  { text: "Be where you are, not where you think you should be.", author: "Unknown", category: "mindfulness" },
  { text: "In today's rush, we all think too much, seek too much, want too much, and forget about the joy of just being.", author: "Eckhart Tolle", category: "mindfulness" },
  { text: "Mindfulness is a way of befriending ourselves and our experience.", author: "Jon Kabat-Zinn", category: "mindfulness" },
  { text: "The mind is everything. What you think, you become.", author: "Buddha", category: "mindfulness" },
  { text: "Wherever you are, be there totally.", author: "Eckhart Tolle", category: "mindfulness" },
  { text: "Do not dwell in the past, do not dream of the future, concentrate the mind on the present moment.", author: "Buddha", category: "mindfulness" },

  // Wellness
  { text: "Almost everything will work again if you unplug it for a few minutes — including you.", author: "Anne Lamott", category: "wellness" },
  { text: "Taking care of yourself doesn't mean me first, it means me too.", author: "L.R. Knost", category: "wellness" },
  { text: "Your calm mind is the ultimate weapon against your challenges.", author: "Bryant McGill", category: "wellness" },
  { text: "You don't have to be positive all the time. It's perfectly okay to feel sad, angry, annoyed, frustrated, or anxious. Having feelings doesn't make you a negative person.", author: "Lori Deschene", category: "wellness" },
  { text: "Healing takes time, and asking for help is a courageous step.", author: "Mariska Hargitay", category: "wellness" },
  { text: "Rest is not idleness, and to lie sometimes on the grass under trees on a summer's day is by no means a waste of time.", author: "John Lubbock", category: "wellness" },
  { text: "The greatest wealth is health.", author: "Virgil", category: "wellness" },

  // Meditation
  { text: "Quiet the mind, and the soul will speak.", author: "Ma Jaya Sati Bhagavati", category: "meditation" },
  { text: "Meditation is not about stopping thoughts, but recognizing that we are more than our thoughts and our feelings.", author: "Arianna Huffington", category: "meditation" },
  { text: "The thing about meditation is: you become more and more you.", author: "David Lynch", category: "meditation" },
  { text: "Feelings come and go like clouds in a windy sky. Conscious breathing is my anchor.", author: "Thich Nhat Hanh", category: "meditation" },
  { text: "In the midst of movement and chaos, keep stillness inside of you.", author: "Deepak Chopra", category: "meditation" },
  { text: "Silence is not empty, it's full of answers.", author: "Unknown", category: "meditation" },
  { text: "When you own your breath, nobody can steal your peace.", author: "Unknown", category: "meditation" },

  // Self-Care
  { text: "You yourself, as much as anybody in the entire universe, deserve your love and affection.", author: "Buddha", category: "self-care" },
  { text: "Nourishing yourself in a way that helps you blossom in the direction you want to go is attainable, and you are worth the effort.", author: "Deborah Day", category: "self-care" },
  { text: "Be gentle with yourself, you're doing the best you can.", author: "Unknown", category: "self-care" },
  { text: "Self-care is how you take your power back.", author: "Lalah Delia", category: "self-care" },
  { text: "An empty lantern provides no light. Self-care is the fuel that allows your light to shine brightly.", author: "Unknown", category: "self-care" },
  { text: "Talk to yourself like someone you love.", author: "Brené Brown", category: "self-care" },
  { text: "You are allowed to be both a masterpiece and a work in progress simultaneously.", author: "Sophia Bush", category: "self-care" },

  // Calming Affirmations
  { text: "I am at peace with what I cannot change.", author: "Affirmation", category: "affirmation" },
  { text: "I choose to let go of what I cannot control and focus on what I can.", author: "Affirmation", category: "affirmation" },
  { text: "I breathe in calm, I breathe out tension.", author: "Affirmation", category: "affirmation" },
  { text: "I am worthy of rest and relaxation.", author: "Affirmation", category: "affirmation" },
  { text: "I trust the timing of my life.", author: "Affirmation", category: "affirmation" },
  { text: "Every breath I take fills me with peace.", author: "Affirmation", category: "affirmation" },
  { text: "I am enough, just as I am.", author: "Affirmation", category: "affirmation" },
  { text: "My mind is calm, my heart is open, my spirit is free.", author: "Affirmation", category: "affirmation" },
  { text: "I give myself permission to slow down and rest.", author: "Affirmation", category: "affirmation" },
  { text: "I release all worry and welcome serenity.", author: "Affirmation", category: "affirmation" },
  { text: "I am growing, healing, and becoming the best version of myself.", author: "Affirmation", category: "affirmation" },

  // Gratitude & Growth
  { text: "Gratitude turns what we have into enough.", author: "Melody Beattie", category: "gratitude" },
  { text: "Every day may not be good, but there is something good in every day.", author: "Alice Morse Earle", category: "gratitude" },
  { text: "The root of joy is gratefulness.", author: "David Steindl-Rast", category: "gratitude" },
  { text: "Start each day with a positive thought and a grateful heart.", author: "Roy T. Bennett", category: "gratitude" },
  { text: "Happiness is not something ready-made. It comes from your own actions.", author: "Dalai Lama", category: "gratitude" },
];

/**
 * Get today's daily quote, rotating based on the date.
 * Returns the same quote for a given calendar day.
 */
export function getDailyQuote() {
  const today = new Date();
  const dayOfYear = Math.floor(
    (today - new Date(today.getFullYear(), 0, 0)) / (1000 * 60 * 60 * 24)
  );
  const index = dayOfYear % DAILY_QUOTES.length;
  return DAILY_QUOTES[index];
}

/**
 * Get a random quote from a specific category (or any category).
 */
export function getRandomQuote(category = null) {
  const pool = category
    ? DAILY_QUOTES.filter(q => q.category === category)
    : DAILY_QUOTES;
  return pool[Math.floor(Math.random() * pool.length)];
}

/**
 * Get all quotes (for browsing or filtering).
 */
export function getAllQuotes() {
  return DAILY_QUOTES;
}

export default DAILY_QUOTES;
