# src/libriscribe/retrieval/keyword_index.py

import json
import math
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple
from libriscribe.retrieval.models import RetrievalChunk, SearchResult

# Optional rank-bm25 import
try:
    from rank_bm25 import BM25Okapi
    HAS_RANK_BM25 = True
except ImportError:
    HAS_RANK_BM25 = False


def tokenize(text: str) -> List[str]:
    """Simple alphanumeric tokenizer that lowercases terms."""
    return re.findall(r"\b\w+\b", text.lower())


class FallbackTFIDFIndex:
    """A pure-Python TF-IDF ranker fallback when rank-bm25 is unavailable."""

    def __init__(self):
        self.doc_term_freqs: List[Dict[str, int]] = []
        self.doc_lengths: List[int] = []
        self.doc_ids: List[str] = []
        self.df: Dict[str, int] = {}
        self.num_docs = 0

    def fit(self, corpus: List[Tuple[str, str]]):
        """Fits TF-IDF weights on a corpus of (doc_id, text) tuples."""
        self.doc_term_freqs = []
        self.doc_lengths = []
        self.doc_ids = []
        self.df = {}
        self.num_docs = len(corpus)

        for doc_id, text in corpus:
            tokens = tokenize(text)
            self.doc_ids.append(doc_id)
            self.doc_lengths.append(len(tokens))

            tf: Dict[str, int] = {}
            for token in tokens:
                tf[token] = tf.get(token, 0) + 1
            self.doc_term_freqs.append(tf)

            # Update document frequency (DF)
            for token in tf:
                self.df[token] = self.df.get(token, 0) + 1

    def score(self, query_tokens: List[str]) -> List[float]:
        """Scores each document against a list of query tokens."""
        scores = [0.0] * self.num_docs
        if self.num_docs == 0 or not query_tokens:
            return scores

        for token in query_tokens:
            if token not in self.df:
                continue

            # Compute IDF: ln(1 + num_docs / doc_frequency)
            idf = math.log(1.0 + (self.num_docs / self.df[token]))

            for i in range(self.num_docs):
                tf = self.doc_term_freqs[i].get(token, 0)
                if tf > 0:
                    # Simple sub-linear TF scaling: 1 + ln(tf)
                    tf_scaled = 1.0 + math.log(tf)
                    scores[i] += tf_scaled * idf

        return scores


class KeywordIndex:
    """Keyword search engine with optional BM25 and fallback TF-IDF."""

    def __init__(self, projects_dir: Path):
        self.projects_dir = projects_dir
        self.chunks_map: Dict[str, RetrievalChunk] = {}
        self.corpus: List[Tuple[str, str]] = []  # List of (chunk_id, searchable_text)
        self.bm25_ranker: Any = None
        self.fallback_ranker: FallbackTFIDFIndex | None = None

    def build(self, chunks: List[RetrievalChunk]) -> None:
        """Builds the index from a list of chunks."""
        self.chunks_map = {c.chunk_id: c for chunk in chunks for c in [chunk]}
        self.corpus = []

        for chunk in chunks:
            # Enrich chunk text with metadata keywords to boost search matches
            metadata_keywords = []
            if chunk.entity_name:
                metadata_keywords.append(f"entity:{chunk.entity_name}")
            for character in chunk.characters:
                metadata_keywords.append(f"char:{character}")
            for loc in chunk.locations:
                metadata_keywords.append(f"location:{loc}")
            for tag in chunk.tags:
                metadata_keywords.append(f"tag:{tag}")

            searchable_text = chunk.text + " " + " ".join(metadata_keywords)
            self.corpus.append((chunk.chunk_id, searchable_text))

        if HAS_RANK_BM25:
            tokenized_corpus = [tokenize(text) for _, text in self.corpus]
            if tokenized_corpus:
                self.bm25_ranker = BM25Okapi(tokenized_corpus)
            else:
                self.bm25_ranker = None
            self.fallback_ranker = None
        else:
            self.fallback_ranker = FallbackTFIDFIndex()
            self.fallback_ranker.fit(self.corpus)
            self.bm25_ranker = None

    def search(
        self,
        query: str,
        top_k: int = 6,
        filters: Dict[str, Any] | None = None,
    ) -> List[SearchResult]:
        """Searches the keyword index and returns top-k results matching filters."""
        if not self.corpus:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        # Get raw scores
        if HAS_RANK_BM25 and self.bm25_ranker:
            scores = self.bm25_ranker.get_scores(query_tokens)
        elif self.fallback_ranker:
            scores = self.fallback_ranker.score(query_tokens)
        else:
            scores = [0.0] * len(self.corpus)

        # Assemble and rank results
        results = []
        for i, (chunk_id, _) in enumerate(self.corpus):
            chunk = self.chunks_map.get(chunk_id)
            if not chunk:
                continue

            # Apply metadata filters
            if filters:
                match = True
                # Match source_type
                if "source_type" in filters:
                    allowed_types = filters["source_type"]
                    if isinstance(allowed_types, list):
                        if chunk.source_type not in allowed_types:
                            match = False
                    elif chunk.source_type != allowed_types:
                        match = False

                # Match chapter_number
                if "chapter_number" in filters:
                    if chunk.chapter_number != filters["chapter_number"]:
                        match = False

                # Match characters
                if "characters" in filters:
                    req_chars = filters["characters"]
                    if isinstance(req_chars, list):
                        if not any(rc in chunk.characters for req_char in req_chars for rc in [req_char]):
                            match = False
                    elif req_chars not in chunk.characters:
                        match = False

                if not match:
                    continue

            score = float(scores[i])
            if score > 0.0 or query.lower() in chunk.text.lower():
                # Add a tiny exact substring bonus to score if query text is present
                if query.lower() in chunk.text.lower():
                    score += 0.5

                results.append(
                    SearchResult(
                        chunk_id=chunk.chunk_id,
                        document_id=chunk.document_id,
                        text=chunk.text,
                        source_type=chunk.source_type,
                        score=score,
                        score_breakdown={"keyword_score": score},
                        chapter_number=chunk.chapter_number,
                        scene_number=chunk.scene_number,
                        entity_name=chunk.entity_name,
                        tags=chunk.tags,
                        characters=chunk.characters,
                        locations=chunk.locations,
                        themes=chunk.themes,
                    )
                )

        # Sort descending by score
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def save_to_file(self, file_path: Path) -> None:
        """Saves index corpus mapping so it can be re-loaded and fit on boot."""
        data = {
            "chunks": [c.model_dump(mode="json") for c in self.chunks_map.values()]
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def load_from_file(self, file_path: Path) -> None:
        """Loads corpus mapping from JSON and rebuilds the BM25/TF-IDF models."""
        if not file_path.exists():
            return

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        chunks = [RetrievalChunk.model_validate(c) for c in data.get("chunks", [])]
        self.build(chunks)
