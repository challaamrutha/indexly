from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Indexly API",
    description="AI-powered search engine for video libraries",
    version="0.1.0",
)

# Allow the Next.js frontend to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    query = data.get("query", "").strip()

    if not query:
        return {
            "query": "",
            "results": [],
            "message": "Please enter a search query.",
        }

    sample_results = [
        {
            "title": "Football Match Highlights",
            "timestamp": "00:02:14",
            "description": "Football match highlights and important moments.",
        },
        {
            "title": "Team Training Session",
            "timestamp": "00:07:32",
            "description": "Players practicing passing and shooting drills.",
        },
        {
            "title": "Championship Final",
            "timestamp": "00:15:48",
            "description": "A key moment from the championship final.",
        },
    ]

    return {
        "query": query,
        "results": sample_results,
        "message": f"Found {len(sample_results)} results for: {query}",
    }
