from pathlib import Path
import json
import re

import numpy as np
from sentence_transformers import SentenceTransformer

from transcribe import transcribe_video


BASE_DIR = Path(__file__).resolve().parent
INDEX_FILE = BASE_DIR / "search_index.json"

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

index = []


def load_index():
    global index

    if not INDEX_FILE.exists():
        index = []
        return

    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as file:
            index = json.load(file)
    except (json.JSONDecodeError, OSError):
        index = []


def save_index():
    with open(INDEX_FILE, "w", encoding="utf-8") as file:
        json.dump(index, file, ensure_ascii=False, indent=2)


def format_timestamp(seconds: float) -> str:
    seconds = max(0, int(seconds))

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    return f"{minutes:02d}:{secs:02d}"


def normalize_text(text: str) -> str:
    return " ".join(text.lower().strip().split())


def tokenize(text: str):
    return re.findall(r"[a-z0-9]+", normalize_text(text))


def index_video(video_path: str, video_url: str, title: str):
    global index

    video_file = Path(video_path)

    if not video_file.exists():
        raise FileNotFoundError(
            f"Video not found: {video_file}"
        )

    print("=" * 60)
    print(f"TRANSCRIBING: {title}")
    print("=" * 60)

    transcript = transcribe_video(str(video_file))

    segments = transcript["segments"]

    if not segments:
        raise ValueError(
            "No speech was detected in the video."
        )

    print(
        f"Whisper found {len(segments)} transcript segments."
    )

    # Remove any previous index entries for this video.
    index = [
        item
        for item in index
        if item["video_url"] != video_url
    ]

    searchable_segments = []
    texts = []

    for segment in segments:
        text = segment["text"].strip()

        if not text:
            continue

        item = {
            "title": title,
            "video_url": video_url,
            "start": float(segment["start"]),
            "end": float(segment["end"]),
            "timestamp": format_timestamp(
                segment["start"]
            ),
            "text": text,
        }

        searchable_segments.append(item)
        texts.append(text)

    if not searchable_segments:
        raise ValueError(
            "No usable transcript segments were found."
        )

    print(
        f"Creating embeddings for "
        f"{len(searchable_segments)} transcript segments..."
    )

    embeddings = embedding_model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    for item, embedding in zip(
        searchable_segments,
        embeddings,
    ):
        item["embedding"] = embedding.tolist()
        index.append(item)

    save_index()

    print(
        f"INDEXED: {title} "
        f"({len(searchable_segments)} segments)"
    )

    return {
        "title": title,
        "video_url": video_url,
        "duration": transcript["duration"],
        "language": transcript["language"],
        "segments_indexed": len(searchable_segments),
    }


def search_videos(query: str, limit=None):
    if not query or not query.strip():
        return []

    if not index:
        return []

    query = query.strip()

    query_embedding = embedding_model.encode(
        query,
        normalize_embeddings=True,
    )

    normalized_query = normalize_text(query)
    query_tokens = set(tokenize(query))

    results = []

    for item in index:
        normalized_text = normalize_text(
            item["text"]
        )

        text_tokens = set(
            tokenize(item["text"])
        )

        semantic_score = float(
            np.dot(
                query_embedding,
                np.array(
                    item["embedding"],
                    dtype=np.float32,
                ),
            )
        )

        exact_phrase = (
            normalized_query in normalized_text
        )

        overlap = (
            len(query_tokens & text_tokens)
            / len(query_tokens)
            if query_tokens
            else 0.0
        )

        score = semantic_score

        if overlap > 0:
            score += 0.10 * overlap

        if exact_phrase:
            score += 0.20

        # Return exact matches, word matches,
        # and genuinely relevant semantic matches.
        if (
            exact_phrase
            or overlap > 0
            or semantic_score >= 0.35
        ):
            results.append(
                {
                    "title": item["title"],
                    "video_url": item["video_url"],
                    "timestamp": item["timestamp"],
                    "start": item["start"],
                    "end": item["end"],
                    "description": item["text"],
                    "score": round(score, 4),
                }
            )

    results.sort(
        key=lambda result: result["score"],
        reverse=True,
    )

    if limit is not None:
        return results[:limit]

    return results


load_index()
