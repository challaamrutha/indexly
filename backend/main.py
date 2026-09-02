from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import shutil

from videos import VIDEOS

app = FastAPI(
    title="Indexly API",
    description="AI-powered search engine for video libraries",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@app.get("/")
def root():
    return {
        "message": "Indexly API is running",
        "status": "ok",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/search")
def search(data: dict):
    query = data.get("query", "").strip().lower()

    if not query:
        return {
            "query": "",
            "results": [],
            "message": "Please enter a search query.",
        }

    results = []

    for video in VIDEOS:
        searchable_text = (
            video["title"] + " " +
            video["description"]
        ).lower()

        if query in searchable_text:
            results.append(video)

    return {
        "query": query,
        "results": results,
        "message": f"Found {len(results)} results for: {query}",
    }


@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    file_path = UPLOAD_DIR / file.filename

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "message": "Video uploaded successfully",
        "filename": file.filename,
        "path": str(file_path),
    }
