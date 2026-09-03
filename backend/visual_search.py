from pathlib import Path
import json
import re

import numpy as np
import torch
from transformers import CLIPModel, CLIPProcessor


BASE_DIR = Path(__file__).resolve().parent
FRAMES_DIR = BASE_DIR / "visual_frames"

CLIP_MODEL_NAME = "openai/clip-vit-base-patch32"

print("Loading CLIP search model...")

clip_processor = CLIPProcessor.from_pretrained(
    CLIP_MODEL_NAME
)

clip_model = CLIPModel.from_pretrained(
    CLIP_MODEL_NAME
)

clip_model.eval()

print("CLIP search model ready.")


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


def create_text_embedding(
    query: str,
):
    inputs = clip_processor(
        text=query,
        return_tensors="pt",
        padding=True,
    )

    with torch.no_grad():
        features = clip_model.get_text_features(
            **inputs
        )

    features = features / features.norm(
        dim=-1,
        keepdim=True,
    )

    return features[0].cpu().numpy()


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

            video_url = metadata.get(
                "video_url",
                "",
            )

            title = metadata.get(
                "title",
                "Untitled video",
            )

            for frame in metadata.get(
                "frames",
                [],
            ):
                frames.append(
                    {
                        "video_id": video_id,
                        "video_url": frame.get(
                            "video_url",
                            video_url,
                        ),
                        "title": frame.get(
                            "title",
                            title,
                        ),
                        "timestamp": frame[
                            "timestamp"
                        ],
                        "image_path": frame[
                            "image_path"
                        ],
                        "ocr_text": frame.get(
                            "ocr_text",
                            "",
                        ),
                        "image_embedding": frame.get(
                            "image_embedding",
                            [],
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

    query_embedding = create_text_embedding(
        query
    )

    normalized_query = normalize_text(
        query
    )

    query_tokens = tokenize(query)

    results = []

    for frame in frames:
        image_embedding = frame[
            "image_embedding"
        ]

        if not image_embedding:
            continue

        visual_score = float(
            np.dot(
                query_embedding,
                np.array(
                    image_embedding,
                    dtype=np.float32,
                ),
            )
        )

        ocr_text = frame["ocr_text"]

        normalized_ocr = normalize_text(
            ocr_text
        )

        text_tokens = tokenize(
            ocr_text
        )

        exact_phrase = (
            bool(ocr_text)
            and normalized_query
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

        ocr_score = overlap

        if exact_phrase:
            ocr_score = 1.0

        combined_score = (
            0.75 * visual_score
            + 0.25 * ocr_score
        )

        if combined_score <= 0:
            continue

        results.append(
            {
                "video_id": frame[
                    "video_id"
                ],
                "video_url": frame[
                    "video_url"
                ],
                "title": frame[
                    "title"
                ],
                "timestamp_seconds": frame[
                    "timestamp"
                ],
                "image_path": frame[
                    "image_path"
                ],
                "ocr_text": ocr_text,
                "visual_score": round(
                    visual_score,
                    4,
                ),
                "ocr_score": round(
                    ocr_score,
                    4,
                ),
                "score": round(
                    combined_score,
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
