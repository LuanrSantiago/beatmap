from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.routes import events
from app.routes import status          # <- adiciona

app = FastAPI(
    title="BeatMap API",
    description="Radar de eventos de música eletrônica",
    version="0.1.0"
)

app.include_router(events.router)
app.include_router(status.router)      # <- adiciona

@app.get("/")
def root():
    return {"message": "BeatMap API funcionando"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "conectado"}