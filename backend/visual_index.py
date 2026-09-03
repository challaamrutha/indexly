from pathlib import Path
import subprocess
import json
import math

import pytesseract
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor


BASE_DIR = Path(__file__).resolve().parent

FRAMES_DIR = BASE_DIR / "visual_frames"
FRAMES_DIR.mkdir(exist_ok=True)


CLIP_MODEL_NAME = "openai/clip-vit-base-patch32"

print("Loading CLIP vision model...")

clip_processor = CLIPProcessor.from_pretrained(
    CLIP_MODEL_NAME
)

clip_model = CLIPModel.from_pretrained(
    CLIP_MODEL_NAME
)

clip_model.eval()

print("CLIP vision model ready.")


def get_video_duration(video_path: str) -> float:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
    )

    return float(result.stdout.strip())


def extract_frame(
    video_path: str,
    output_path: Path,
    timestamp: float,
):
    command = [
        "ffmpeg",
        "-y",
        "-ss",
        str(timestamp),
        "-i",
        video_path,
        "-frames:v",
        "1",
        "-vf",
        "scale=1280:-2",
        "-q:v",
        "3",
        str(output_path),
    ]

    subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )


def extract_ocr(image_path: Path) -> str:
    try:
        with Image.open(image_path) as image:
            text = pytesseract.image_to_string(
                image,
                config="--psm 6",
            )

        return " ".join(text.split())

    except Exception as error:
        print(
            f"OCR failed for {image_path}: {error}"
        )
        return ""


def create_image_embedding(
    image_path: Path,
):
    try:
        with Image.open(image_path) as image:
            image = image.convert("RGB")

            inputs = clip_processor(
                images=image,
                return_tensors="pt",
            )

        with torch.no_grad():
            features = clip_model.get_image_features(
                **inputs
            )

        features = features / features.norm(
            dim=-1,
            keepdim=True,
        )

        return features[0].cpu().tolist()

    except Exception as error:
        print(
            f"Vision embedding failed for "
            f"{image_path}: {error}"
        )
        return []


def sample_video_frames(
    video_path: str,
    video_id: str,
    video_url: str,
    title: str,
    interval_seconds: float = 5.0,
):
    video_file = Path(video_path)

    if not video_file.exists():
        raise FileNotFoundError(
            f"Video not found: {video_file}"
        )

    duration = get_video_duration(
        str(video_file)
    )

    video_frames_dir = (
        FRAMES_DIR / video_id
    )

    video_frames_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    frame_count = max(
        1,
        math.ceil(
            duration / interval_seconds
        ),
    )

    frames = []

    for index in range(frame_count):
        timestamp = (
            index * interval_seconds
        )

        if timestamp >= duration:
            timestamp = max(
                0,
                duration - 0.1,
            )

        image_path = (
            video_frames_dir
            / f"frame_{index:06d}.jpg"
        )

        print(
            f"Extracting frame "
            f"{index + 1}/{frame_count} "
            f"at {timestamp:.1f}s"
        )

        extract_frame(
            str(video_file),
            image_path,
            timestamp,
        )

        print(
            f"Running OCR at {timestamp:.1f}s"
        )

        ocr_text = extract_ocr(
            image_path
        )

        print(
            f"Creating visual embedding "
            f"at {timestamp:.1f}s"
        )

        image_embedding = (
            create_image_embedding(
                image_path
            )
        )

        frames.append(
            {
                "video_id": video_id,
                "video_url": video_url,
                "title": title,
                "timestamp": round(
                    timestamp,
                    3,
                ),
                "image_path": str(
                    image_path
                ),
                "ocr_text": ocr_text,
                "image_embedding": image_embedding,
            }
        )

    metadata_path = (
        video_frames_dir
        / "metadata.json"
    )

    with open(
        metadata_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            {
                "video_id": video_id,
                "video_url": video_url,
                "title": title,
                "video_path": str(
                    video_file
                ),
                "duration": duration,
                "interval_seconds": (
                    interval_seconds
                ),
                "frames": frames,
            },
            file,
            ensure_ascii=False,
            indent=2,
        )

    return {
        "video_id": video_id,
        "video_url": video_url,
        "title": title,
        "duration": duration,
        "frames": frames,
        "frame_count": len(frames),
    }
