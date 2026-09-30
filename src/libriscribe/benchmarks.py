"""Reproducible local quality diagnostics using a checked-in fixture corpus."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from statistics import mean
from typing import Any

from libriscribe.retrieval.keyword_index import FallbackTFIDFIndex, tokenize


DEFAULT_FIXTURE = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "quality_benchmark.json"


def run_benchmarks(fixture_path: Path = DEFAULT_FIXTURE, k: int = 3) -> dict[str, Any]:
    if isinstance(k, bool) or not isinstance(k, int) or not 1 <= k <= 100:
        raise ValueError("k must be between 1 and 100")
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    documents = fixture["retrieval_documents"]
    index = FallbackTFIDFIndex()
    index.fit([(item["id"], item["text"]) for item in documents])
    recalls: list[float] = []
    precisions: list[float] = []
    reciprocal_ranks: list[float] = []
    for case in fixture["retrieval_queries"]:
        scores = index.score(tokenize(case["query"]))
        ranked = [documents[i]["id"] for i in sorted(range(len(scores)), key=lambda i: (-scores[i], documents[i]["id"])) if scores[i] > 0]
        relevant = set(case["relevant_ids"])
        top = ranked[:k]
        recalls.append(len(relevant.intersection(top)) / len(relevant) if relevant else 1.0)
        precisions.append(len(relevant.intersection(top)) / k)
        reciprocal_ranks.append(next((1.0 / rank for rank, doc_id in enumerate(ranked, 1) if doc_id in relevant), 0.0))

    texts = fixture["writing_samples"]
    sentence_counts: list[int] = []
    sentence_lengths: list[int] = []
    type_token_ratios: list[float] = []
    repeated_sentence_rates: list[float] = []
    total_words = 0
    for text in texts:
        words = tokenize(text)
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.strip()) if part.strip()]
        normalized = [re.sub(r"\W+", " ", sentence.lower()).strip() for sentence in sentences]
        sentence_counts.append(len(sentences))
        sentence_lengths.extend(len(tokenize(sentence)) for sentence in sentences)
        type_token_ratios.append(len(set(words)) / len(words) if words else 0.0)
        repeated_sentence_rates.append((len(normalized) - len(set(normalized))) / len(normalized) if normalized else 0.0)
        total_words += len(words)

    return {
        "retrieval": {
            "queries": len(fixture["retrieval_queries"]),
            f"recall_at_{k}": round(mean(recalls), 4) if recalls else 0.0,
            f"precision_at_{k}": round(mean(precisions), 4) if precisions else 0.0,
            "mean_reciprocal_rank": round(mean(reciprocal_ranks), 4) if reciprocal_ranks else 0.0,
        },
        "writing_diagnostics": {
            "samples": len(texts),
            "words": total_words,
            "sentences": sum(sentence_counts),
            "mean_words_per_sentence": round(mean(sentence_lengths), 2) if sentence_lengths else 0.0,
            "mean_type_token_ratio": round(mean(type_token_ratios), 4) if type_token_ratios else 0.0,
            "mean_repeated_sentence_rate": round(mean(repeated_sentence_rates), 4) if repeated_sentence_rates else 0.0,
        },
        "notes": "Deterministic lexical diagnostics; these measures are not a substitute for human writing review.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run deterministic local retrieval and writing diagnostics.")
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--k", type=int, default=3)
    args = parser.parse_args()
    print(json.dumps(run_benchmarks(args.fixture, args.k), indent=2))


if __name__ == "__main__":
    main()
