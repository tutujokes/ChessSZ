

from fastapi import FastAPI
from routes.analysis import router as analysis_router

app = FastAPI()

@app.get("/api/health")
def health():
    return {"status": "ok"}

app.include_router(analysis_router, prefix="/api")

