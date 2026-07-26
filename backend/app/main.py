from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.routes import events, status

app = FastAPI(
    title="BeatMap API",
    description="Radar de eventos de música eletrônica",
    version="0.1.0"
)

# CORS — permite que o frontend (porta 5173) fale com o backend (porta 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://beatmap-lake.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(events.router)
app.include_router(status.router)

@app.get("/")
def root():
    return {"message": "BeatMap API funcionando"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "conectado"}