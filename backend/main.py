from pathlib import Path
import shutil
import uuid

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from search_engine import index_video, search_videos
from visual_index import sample_video_frames
from visual_search import search_visuals


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


BASE_DIR = Path(__file__).resolve().parent

UPLOAD_DIR = BASE_DIR / "uploads"
FRAMES_DIR = BASE_DIR / "visual_frames"

UPLOAD_DIR.mkdir(exist_ok=True)
FRAMES_DIR.mkdir(exist_ok=True)


app.mount(
    "/uploads",
    StaticFiles(directory=str(UPLOAD_DIR)),
    name="uploads",
)

app.mount(
    "/visual-frames",
    StaticFiles(directory=str(FRAMES_DIR)),
    name="visual-frames",
)


@app.get("/")
def root():
    return {
        "message": "Indexly API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


def normalize_score(
    score: float,
    minimum: float,
    maximum: float,
) -> float:
    if maximum <= minimum:
        return 0.5

    normalized = (
        score - minimum
    ) / (
        maximum - minimum
    )

    return max(
        0.0,
        min(
            1.0,
            normalized,
        ),
    )


def combine_results(
    transcript_results,
    visual_results,
):
    combined = []

    transcript_scores = [
        float(result.get("score", 0.0))
        for result in transcript_results
    ]

    visual_scores = [
        float(result.get("score", 0.0))
        for result in visual_results
    ]

    transcript_min = (
        min(transcript_scores)
        if transcript_scores
        else 0.0
    )

    transcript_max = (
        max(transcript_scores)
        if transcript_scores
        else 1.0
    )

    visual_min = (
        min(visual_scores)
        if visual_scores
        else 0.0
    )

    visual_max = (
        max(visual_scores)
        if visual_scores
        else 1.0
    )

    for result in transcript_results:
        normalized_score = normalize_score(
            float(result.get("score", 0.0)),
            transcript_min,
            transcript_max,
        )

        combined.append(
            {
                "type": "transcript",
                "title": result["title"],
                "video_url": result[
                    "video_url"
                ],
                "timestamp": result[
                    "timestamp"
                ],
                "start": result[
                    "start"
                ],
                "end": result[
                    "end"
                ],
                "description": result[
                    "description"
                ],
                "score": round(
                    normalized_score,
                    4,
                ),
                "speech_score": round(
                    normalized_score,
                    4,
                ),
                "visual_score": 0.0,
                "ocr_score": 0.0,
            }
        )

    for result in visual_results:
        normalized_visual_score = (
            normalize_score(
                float(
                    result.get(
                        "visual_score",
                        result.get(
                            "score",
                            0.0,
                        ),
                    )
                ),
                visual_min,
                visual_max,
            )
        )

        ocr_score = float(
            result.get(
                "ocr_score",
                0.0,
            )
        )

        visual_score = float(
            result.get(
                "visual_score",
                result.get(
                    "score",
                    0.0,
                ),
            )
        )

        combined_visual_score = (
            0.75
            * normalized_visual_score
            + 0.25
            * ocr_score
        )

        combined.append(
            {
                "type": "visual",
                "title": result[
                    "title"
                ],
                "video_id": result[
                    "video_id"
                ],
                "video_url": result[
                    "video_url"
                ],
                "timestamp_seconds": result[
                    "timestamp_seconds"
                ],
                "timestamp": format_timestamp(
                    result[
                        "timestamp_seconds"
                    ]
                ),
                "start": result[
                    "timestamp_seconds"
                ],
                "end": result[
                    "timestamp_seconds"
                ],
                "description": result[
                    "ocr_text"
                ],
                "thumbnail_url": (
                    build_thumbnail_url(
                        result[
                            "image_path"
                        ]
                    )
                ),
                "score": round(
                    combined_visual_score,
                    4,
                ),
                "speech_score": 0.0,
                "visual_score": round(
                    normalized_visual_score,
                    4,
                ),
                "ocr_score": round(
                    ocr_score,
                    4,
                ),
            }
        )

    combined.sort(
        key=lambda result: result[
            "score"
        ],
        reverse=True,
    )

    return combined


def build_thumbnail_url(
    image_path: str,
) -> str:
    image_path = Path(
        image_path
    )

    try:
        relative_path = (
            image_path.relative_to(
                FRAMES_DIR
            )
        )

        return (
            "/visual-frames/"
            + str(relative_path)
        )

    except ValueError:
        return ""


@app.post("/search")
def search(data: dict):
    query = data.get(
        "query",
        "",
    ).strip()

    if not query:
        return {
            "results": []
        }

    transcript_results = search_videos(
        query=query
    )

    visual_results = search_visuals(
        query=query
    )

    results = combine_results(
        transcript_results,
        visual_results,
    )

    return {
        "query": query,
        "results": results,
        "total": len(results),
    }


@app.post("/upload")
async def upload_video(
    file: UploadFile = File(...)
):
    if not file.filename:
        return {
            "error": "No filename provided"
        }

    original_filename = Path(
        file.filename
    ).name

    video_id = uuid.uuid4().hex

    unique_name = (
        f"{video_id}_{original_filename}"
    )

    video_path = (
        UPLOAD_DIR / unique_name
    )

    with open(
        video_path,
        "wb",
    ) as buffer:
        shutil.copyfileobj(
            file.file,
            buffer,
        )

    video_url = (
        f"/uploads/{unique_name}"
    )

    print("=" * 60)
    print(
        f"UPLOADED: "
        f"{original_filename}"
    )
    print(
        f"VIDEO ID: {video_id}"
    )
    print(
        f"SAVED: {video_path}"
    )
    print("=" * 60)

    try:
        transcript_result = index_video(
            video_path=str(
                video_path
            ),
            video_url=video_url,
            title=original_filename,
        )

        print("=" * 60)
        print("CREATING VISUAL INDEX")
        print("=" * 60)

        visual_result = (
            sample_video_frames(
                video_path=str(
                    video_path
                ),
                video_id=video_id,
                video_url=video_url,
                title=original_filename,
                interval_seconds=5.0,
            )
        )

        print(
            f"VISUAL FRAMES: "
            f"{visual_result['frame_count']}"
        )

    except Exception as error:
        print(
            f"Indexing failed: {error}"
        )

        if video_path.exists():
            video_path.unlink()

        return {
            "error": str(error)
        }

    return {
        "message": (
            "Video uploaded and "
            "indexed successfully"
        ),
        "video_id": video_id,
        "filename": original_filename,
        "path": video_url,
        "video_url": video_url,
        "duration": transcript_result[
            "duration"
        ],
        "language": transcript_result[
            "language"
        ],
        "segments_indexed": (
            transcript_result[
                "segments_indexed"
            ]
        ),
        "visual_frames_indexed": (
            visual_result[
                "frame_count"
            ]
        ),
    }


def format_timestamp(
    seconds: float
) -> str:
    seconds = max(
        0,
        int(seconds),
    )

    hours = seconds // 3600
    minutes = (
        seconds % 3600
    ) // 60
    secs = seconds % 60

    if hours > 0:
        return (
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{secs:02d}"
        )

    return (
        f"{minutes:02d}:"
        f"{secs:02d}"
    )
