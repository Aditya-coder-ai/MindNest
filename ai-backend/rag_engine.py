"""
╔══════════════════════════════════════════════════════════════════╗
║   MindNest — RAG Engine (Retrieval-Augmented Generation)        ║
║                                                                  ║
║   Uses TF-IDF vectorization + cosine similarity to retrieve     ║
║   relevant mental health knowledge based on the user's journal  ║
║   entry and detected emotion. Augments the AI response with     ║
║   evidence-based techniques, practices, and academic sources.   ║
║                                                                  ║
║   Architecture:                                                  ║
║     1. Load knowledge base (JSON documents)                     ║
║     2. Build TF-IDF index over all document content             ║
║     3. On query: combine user text + emotion context            ║
║     4. Retrieve top-K most relevant documents                   ║
║     5. Return structured context for the API response           ║
║                                                                  ║
║   No external APIs needed — fully local retrieval.              ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ═════════════════════════════════════════════════════════════════
#  RAG Engine Class
# ═════════════════════════════════════════════════════════════════

class RAGEngine:
    """
    Retrieval-Augmented Generation engine for MindNest.

    Indexes a mental health knowledge base using TF-IDF vectors,
    then retrieves the most relevant documents for a given journal
    entry and detected emotion.
    """

    def __init__(self, knowledge_base_path=None):
        """Initialize the RAG engine with a knowledge base file."""
        if knowledge_base_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            knowledge_base_path = os.path.join(base_dir, "data", "knowledge_base.json")

        self.kb_path = knowledge_base_path
        self.documents = []
        self.doc_texts = []       # Combined text for TF-IDF
        self.vectorizer = None
        self.tfidf_matrix = None
        self.ready = False

        self._load_and_index()

    def _load_and_index(self):
        """Load the knowledge base and build the TF-IDF index."""
        try:
            with open(self.kb_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.documents = data.get("documents", [])

            if not self.documents:
                print("   ⚠️  RAG: Knowledge base is empty")
                return

            # Build searchable text for each document:
            #   Combine title + content + emotions + category for richer matching
            self.doc_texts = []
            for doc in self.documents:
                combined = " ".join([
                    doc.get("title", ""),
                    doc.get("content", ""),
                    " ".join(doc.get("emotions", [])),
                    doc.get("category", ""),
                    doc.get("title", ""),  # Double-weight the title
                ])
                self.doc_texts.append(combined)

            # Build TF-IDF index
            self.vectorizer = TfidfVectorizer(
                max_features=3000,
                ngram_range=(1, 2),
                stop_words="english",
                sublinear_tf=True,
            )
            self.tfidf_matrix = self.vectorizer.fit_transform(self.doc_texts)

            self.ready = True
            print(f"   📚 RAG Engine ready: {len(self.documents)} knowledge documents indexed")

        except FileNotFoundError:
            print(f"   ⚠️  RAG: Knowledge base not found at {self.kb_path}")
        except json.JSONDecodeError as e:
            print(f"   ⚠️  RAG: Invalid JSON in knowledge base: {e}")
        except Exception as e:
            print(f"   ⚠️  RAG: Failed to initialize: {e}")

    def retrieve(self, query_text, detected_emotion=None, top_k=3):
        """
        Retrieve the most relevant knowledge documents.

        Args:
            query_text (str): The user's journal entry text
            detected_emotion (str): The detected emotion category
            top_k (int): Number of documents to retrieve

        Returns:
            list[dict]: Top-K relevant documents with similarity scores
        """
        if not self.ready or not query_text.strip():
            return []

        # Build an enriched query: user text + emotion context
        # This helps bias retrieval toward emotion-relevant content
        enriched_query = query_text
        if detected_emotion:
            enriched_query = f"{detected_emotion} {detected_emotion} {query_text}"

        # Vectorize the query
        query_vector = self.vectorizer.transform([enriched_query])

        # Compute cosine similarity against all documents
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()

        # Also apply emotion-based boosting / penalizing
        if detected_emotion:
            for i, doc in enumerate(self.documents):
                doc_emotions = doc.get("emotions", [])
                if detected_emotion in doc_emotions:
                    similarities[i] *= 2.0  # 2x boost for emotion match
                else:
                    similarities[i] *= 0.3  # Penalize non-matching emotions

        # Get top-K indices (sorted by similarity, descending)
        top_indices = similarities.argsort()[::-1][:top_k]

        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score < 0.01:  # Skip near-zero relevance
                continue

            doc = self.documents[idx]
            results.append({
                "id": doc.get("id", ""),
                "title": doc.get("title", ""),
                "content": doc.get("content", ""),
                "category": doc.get("category", ""),
                "emotions": doc.get("emotions", []),
                "source": doc.get("source", ""),
                "relevance": round(score, 4),
            })

        return results

    def get_augmented_response(self, query_text, detected_emotion=None, top_k=2):
        """
        Get a structured RAG-augmented response.

        Returns a dict containing retrieved context formatted for the API response.
        """
        retrieved = self.retrieve(query_text, detected_emotion, top_k=top_k)

        if not retrieved:
            return {
                "ragEnabled": False,
                "retrievedContext": [],
                "contextSummary": None,
            }

        # Build a context summary from retrieved documents
        summaries = []
        for doc in retrieved:
            summaries.append(f"{doc['title']}: {doc['content'][:150]}...")

        context_summary = " | ".join(summaries)

        return {
            "ragEnabled": True,
            "retrievedContext": [
                {
                    "title": doc["title"],
                    "content": doc["content"],
                    "category": doc["category"],
                    "source": doc["source"],
                    "relevance": doc["relevance"],
                }
                for doc in retrieved
            ],
            "contextSummary": context_summary[:500],
        }

    def get_stats(self):
        """Return stats about the RAG engine."""
        return {
            "ready": self.ready,
            "totalDocuments": len(self.documents),
            "vocabularySize": len(self.vectorizer.vocabulary_) if self.vectorizer else 0,
            "categories": list(set(d.get("category", "") for d in self.documents)),
        }
