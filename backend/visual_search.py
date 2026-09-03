from pathlib import Path
import json
import re


BASE_DIR = Path(__file__).resolve().parent
FRAMES_DIR = BASE_DIR / "visual_frames"


def normalize_text(text: str) -> str:
    return " ".join(
        text.lower().strip().split()
    )


def tokenize(text: str):
    return set(
        re.findall(
            r"[a-z0-9]+",
            normalize_text(text),
        )
    )


def load_visual_index():
    frames = []

    if not FRAMES_DIR.exists():
        return frames

    for video_dir in FRAMES_DIR.iterdir():
        if not video_dir.is_dir():
            continue

        metadata_path = (
            video_dir / "metadata.json"
        )

        if not metadata_path.exists():
            continue

        try:
            with open(
                metadata_path,
                "r",
                encoding="utf-8",
            ) as file:
                metadata = json.load(file)

            video_id = metadata["video_id"]

            for frame in metadata.get(
                "frames",
                [],
            ):
                image_path = Path(
                    frame["image_path"]
                )

                frames.append(
                    {
                        "video_id": video_id,
                        "timestamp": frame[
                            "timestamp"
                        ],
                        "image_path": str(
                            image_path
                        ),
                        "ocr_text": frame.get(
                            "ocr_text",
                            "",
                        ),
                    }
                )

        except (
            json.JSONDecodeError,
            OSError,
            KeyError,
        ):
            continue

    return frames


def search_visuals(
    query: str,
    limit=None,
):
    query = query.strip()

    if not query:
        return []

    frames = load_visual_index()

    if not frames:
        return []

    normalized_query = normalize_text(
        query
    )

    query_tokens = tokenize(query)

    results = []

    for frame in frames:
        ocr_text = frame["ocr_text"]

        if not ocr_text:
            continue

        normalized_ocr = normalize_text(
            ocr_text
        )

        text_tokens = tokenize(
            ocr_text
        )

        exact_phrase = (
            normalized_query
            in normalized_ocr
        )

        overlap = (
            len(
                query_tokens
                & text_tokens
            )
            / len(query_tokens)
            if query_tokens
            else 0.0
        )

        if exact_phrase:
            score = 1.0
        else:
            score = overlap

        if score <= 0:
            continue

        results.append(
            {
                "video_id": frame[
                    "video_id"
                ],
                "timestamp_seconds": frame[
                    "timestamp"
                ],
                "image_path": frame[
                    "image_path"
                ],
                "ocr_text": ocr_text,
                "score": round(
                    score,
                    4,
                ),
            }
        )

    results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    if limit is not None:
        return results[:limit]

    return results
