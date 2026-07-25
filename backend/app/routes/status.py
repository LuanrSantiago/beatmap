from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.models.status import UserEventStatus
from app.models.event import Event
from app.schemas.status import StatusIn, StatusOut
from app.auth import get_current_user_id

router = APIRouter(prefix="/status", tags=["status"])


@router.post("/", response_model=StatusOut)
def set_status(
    payload: StatusIn,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    evento = db.query(Event).filter(Event.id == payload.event_id).first()
    if not evento:
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    registro = (
        db.query(UserEventStatus)
        .filter_by(user_id=user_id, event_id=payload.event_id)
        .first()
    )

    if registro:
        registro.status = payload.status
    else:
        registro = UserEventStatus(
            user_id=user_id,
            event_id=payload.event_id,
            status=payload.status
        )
        db.add(registro)

    db.commit()
    db.refresh(registro)
    return registro


@router.get("/", response_model=list[StatusOut])
def list_status(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    return (
        db.query(UserEventStatus)
        .filter_by(user_id=user_id)
        .all()
    )


@router.delete("/{event_id}", status_code=204)
def delete_status(
    event_id: UUID,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    registro = (
        db.query(UserEventStatus)
        .filter_by(user_id=user_id, event_id=event_id)
        .first()
    )
    if not registro:
        raise HTTPException(status_code=404, detail="Status não encontrado")
    db.delete(registro)
    db.commit()