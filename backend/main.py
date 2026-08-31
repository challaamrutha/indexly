from fastapi import FastAPI

app = FastAPI(
    title="Indexly API",
    description="AI-powered search engine for video libraries",
    version="0.1.0",
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