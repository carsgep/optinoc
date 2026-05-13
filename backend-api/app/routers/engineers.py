from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.support import Engineer
from app.schemas.support import EngineerCreate, EngineerRead, EngineerUpdate

router = APIRouter(prefix="/engineers", tags=["Engineers"])


@router.get("/", response_model=list[EngineerRead])
def list_engineers(db: Session = Depends(get_db)):
    return (
        db.query(Engineer)
        .order_by(Engineer.full_name.asc())
        .all()
    )


@router.post("/", response_model=EngineerRead, status_code=status.HTTP_201_CREATED)
def create_engineer(payload: EngineerCreate, db: Session = Depends(get_db)):
    engineer = Engineer(**payload.model_dump())
    db.add(engineer)
    db.commit()
    db.refresh(engineer)

    return engineer


@router.get("/{engineer_id}", response_model=EngineerRead)
def get_engineer(engineer_id: int, db: Session = Depends(get_db)):
    engineer = db.query(Engineer).filter(Engineer.id == engineer_id).first()

    if not engineer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingeniero no encontrado.",
        )

    return engineer


@router.put("/{engineer_id}", response_model=EngineerRead)
def update_engineer(
    engineer_id: int,
    payload: EngineerUpdate,
    db: Session = Depends(get_db),
):
    engineer = db.query(Engineer).filter(Engineer.id == engineer_id).first()

    if not engineer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingeniero no encontrado.",
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(engineer, field, value)

    db.commit()
    db.refresh(engineer)

    return engineer