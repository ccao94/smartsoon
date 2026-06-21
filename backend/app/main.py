from fastapi import FastAPI
from app.routers import extract, rag

app = FastAPI(title="SmartSoon API", version="0.1.0")


@app.get("/health")
def health_check():
    """Endpoint de healthcheck pour la CI et le monitoring."""
    return {"status": "ok"}


app.include_router(extract.router)
app.include_router(rag.router)