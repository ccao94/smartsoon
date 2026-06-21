from fastapi import FastAPI
from app.routers import rag

app = FastAPI(title="SmartSoon API", version="0.1.0")

@app.get("/health")
def health_check():
    return {"status": "ok"}

app.include_router(rag.router)