from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.support import AlertType
from app.schemas.support import AlertTypeCreate, AlertTypeRead, AlertTypeUpdate

router = APIRouter(prefix="/alert-types", tags=["Alert Types"])


@router.get("/", response_model=list[AlertTypeRead])
def list_alert_types(db: Session = Depends(get_db)):
    return (
        db.query(AlertType)
        .order_by(AlertType.code.asc())
        .all()
    )


@router.post("/", response_model=AlertTypeRead, status_code=status.HTTP_201_CREATED)
def create_alert_type(payload: AlertTypeCreate, db: Session = Depends(get_db)):
    normalized_code = payload.code.strip().upper()

    existing = (
        db.query(AlertType)
        .filter(AlertType.code == normalized_code)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un tipo de alerta con ese código.",
        )

    alert_type = AlertType(
        **payload.model_dump(exclude={"code"}),
        code=normalized_code,
    )

    db.add(alert_type)
    db.commit()
    db.refresh(alert_type)

    return alert_type


@router.get("/{alert_type_id}", response_model=AlertTypeRead)
def get_alert_type(alert_type_id: int, db: Session = Depends(get_db)):
    alert_type = db.query(AlertType).filter(AlertType.id == alert_type_id).first()

    if not alert_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de alerta no encontrado.",
        )

    return alert_type


@router.put("/{alert_type_id}", response_model=AlertTypeRead)
def update_alert_type(
    alert_type_id: int,
    payload: AlertTypeUpdate,
    db: Session = Depends(get_db),
):
    alert_type = db.query(AlertType).filter(AlertType.id == alert_type_id).first()

    if not alert_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de alerta no encontrado.",
        )

    update_data = payload.model_dump(exclude_unset=True)

    if "code" in update_data and update_data["code"]:
        update_data["code"] = update_data["code"].strip().upper()

    for field, value in update_data.items():
        setattr(alert_type, field, value)

    db.commit()
    db.refresh(alert_type)

    return alert_type