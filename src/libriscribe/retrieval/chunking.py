# src/libriscribe/retrieval/chunking.py

from typing import List
from libriscribe.retrieval.models import RetrievalDocument, RetrievalChunk


def estimate_tokens(text: str) -> int:
    """Estimates the number of tokens in a text.

    Uses a robust 4 characters per token heuristic.
    """
    return len(text) // 4


def split_text_by_paragraphs_or_sentences(
    text: str, chunk_size: int = 800, chunk_overlap: int = 120
) -> List[str]:
    """Splits text into chunks of roughly chunk_size characters with overlap,

    attempting to respect paragraph and sentence boundaries.
    """
    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    # Split by paragraphs first
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = []
    current_length = 0

    for para in paragraphs:
        para_len = len(para)
        if not para.strip():
            continue

        # If a single paragraph is larger than chunk_size, we split it by sentences
        if para_len > chunk_size:
            # First, flush whatever we have in current_chunk
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_length = 0

            # Split by sentences (simple period boundary matching)
            sentences = re_split_sentences(para)
            sub_chunk = []
            sub_len = 0
            for sentence in sentences:
                sent_len = len(sentence)
                if sub_len + sent_len > chunk_size:
                    if sub_chunk:
                        chunks.append(" ".join(sub_chunk))
                    # Handle overlap by taking previous sentences
                    overlap_size = 0
                    overlap_chunk = []
                    for s in reversed(sub_chunk):
                        if overlap_size + len(s) < chunk_overlap:
                            overlap_chunk.insert(0, s)
                            overlap_size += len(s)
                        else:
                            break
                    sub_chunk = overlap_chunk + [sentence]
                    sub_len = sum(len(s) for s in sub_chunk)
                else:
                    sub_chunk.append(sentence)
                    sub_len += sent_len
            if sub_chunk:
                chunks.append(" ".join(sub_chunk))
        else:
            # Check if adding this paragraph exceeds chunk_size
            if current_length + para_len > chunk_size:
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                # Handle overlap
                overlap_size = 0
                overlap_chunk = []
                for p in reversed(current_chunk):
                    if overlap_size + len(p) < chunk_overlap:
                        overlap_chunk.insert(0, p)
                        overlap_size += len(p)
                    else:
                        break
                current_chunk = overlap_chunk + [para]
                current_length = sum(len(p) for p in current_chunk)
            else:
                current_chunk.append(para)
                current_length += para_len

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks


def re_split_sentences(text: str) -> List[str]:
    """Helper to split text into sentences using simple regex."""
    import re

    sentence_end = re.compile(r"(?<=[.!?])\s+")
    parts = sentence_end.split(text)
    return [p.strip() for p in parts if p.strip()]


def chunk_document(
    doc: RetrievalDocument, chunk_size: int = 800, chunk_overlap: int = 120
) -> List[RetrievalChunk]:
    """Chunks a RetrievalDocument into multiple RetrievalChunk objects based on source_type rules."""
    chunks_text = []

    # Apply type-specific chunking rules
    if doc.source_type in [
        "project_metadata",
        "chapter_summary",
        "scene_summary",
    ]:
        chunks_text = [doc.text]
    elif doc.source_type == "character_profile":
        # Usually character profiles are short, keep in one chunk, but split if extremely long
        chunks_text = split_text_by_paragraphs_or_sentences(
            doc.text, chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
    elif doc.source_type == "worldbuilding":
        # Worldbuilding entries are split per field, so they are already quite focused.
        # Still split if extremely long.
        chunks_text = split_text_by_paragraphs_or_sentences(
            doc.text, chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
    elif doc.source_type == "chapter_text":
        # Full prose - split by paragraphs/sentences cleanly
        chunks_text = split_text_by_paragraphs_or_sentences(
            doc.text, chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
    else:
        # Default fallback splitter
        chunks_text = split_text_by_paragraphs_or_sentences(
            doc.text, chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )

    ret_chunks = []
    for i, text in enumerate(chunks_text):
        # Generate a unique chunk_id
        chunk_id = f"{doc.document_id}_chunk_{i}"
        # Build token estimate
        tokens = estimate_tokens(text)

        chunk = RetrievalChunk(
            chunk_id=chunk_id,
            document_id=doc.document_id,
            project_name=doc.project_name,
            text=text,
            source_type=doc.source_type,
            chunk_index=i,
            chapter_number=doc.chapter_number,
            scene_number=doc.scene_number,
            entity_name=doc.entity_name,
            tags=doc.tags,
            characters=doc.characters,
            locations=doc.locations,
            themes=doc.themes,
            token_estimate=tokens,
            hash=doc.hash,  # use parent doc hash for chunk-level consistency tracking
        )
        ret_chunks.append(chunk)

    return ret_chunks
