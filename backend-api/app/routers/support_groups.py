from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.support import SupportGroup
from app.schemas.support import SupportGroupCreate, SupportGroupRead, SupportGroupUpdate

router = APIRouter(prefix="/support-groups", tags=["Support Groups"])


@router.get("/", response_model=list[SupportGroupRead])
def list_support_groups(db: Session = Depends(get_db)):
    return (
        db.query(SupportGroup)
        .order_by(SupportGroup.name.asc())
        .all()
    )


@router.post("/", response_model=SupportGroupRead, status_code=status.HTTP_201_CREATED)
def create_support_group(payload: SupportGroupCreate, db: Session = Depends(get_db)):
    existing = (
        db.query(SupportGroup)
        .filter(SupportGroup.name == payload.name)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un grupo de soporte con ese nombre.",
        )

    group = SupportGroup(**payload.model_dump())
    db.add(group)
    db.commit()
    db.refresh(group)

    return group


@router.get("/{group_id}", response_model=SupportGroupRead)
def get_support_group(group_id: int, db: Session = Depends(get_db)):
    group = db.query(SupportGroup).filter(SupportGroup.id == group_id).first()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo de soporte no encontrado.",
        )

    return group


@router.put("/{group_id}", response_model=SupportGroupRead)
def update_support_group(
    group_id: int,
    payload: SupportGroupUpdate,
    db: Session = Depends(get_db),
):
    group = db.query(SupportGroup).filter(SupportGroup.id == group_id).first()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo de soporte no encontrado.",
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(group, field, value)

    db.commit()
    db.refresh(group)

    return group