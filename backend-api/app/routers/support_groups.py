from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.support import Engineer, SupportGroup, SupportGroupMember
from app.schemas.support import (
    GroupMemberCreate,
    GroupMemberRead,
    GroupMemberUpdate,
    SupportGroupCreate,
    SupportGroupRead,
    SupportGroupUpdate,
)

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


@router.get("/{group_id}/members", response_model=list[GroupMemberRead])
def list_group_members(group_id: int, db: Session = Depends(get_db)):
    group = db.query(SupportGroup).filter(SupportGroup.id == group_id).first()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo de soporte no encontrado.",
        )

    return (
        db.query(SupportGroupMember)
        .filter(SupportGroupMember.support_group_id == group_id)
        .order_by(SupportGroupMember.id.asc())
        .all()
    )


@router.post(
    "/{group_id}/members",
    response_model=GroupMemberRead,
    status_code=status.HTTP_201_CREATED,
)
def add_group_member(
    group_id: int,
    payload: GroupMemberCreate,
    db: Session = Depends(get_db),
):
    if payload.support_group_id != group_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El support_group_id del cuerpo no coincide con el group_id de la URL.",
        )

    group = db.query(SupportGroup).filter(SupportGroup.id == group_id).first()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo de soporte no encontrado.",
        )

    engineer = (
        db.query(Engineer)
        .filter(Engineer.id == payload.engineer_id)
        .filter(Engineer.active == True)
        .first()
    )

    if not engineer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingeniero no encontrado o inactivo.",
        )

    existing = (
        db.query(SupportGroupMember)
        .filter(SupportGroupMember.support_group_id == group_id)
        .filter(SupportGroupMember.engineer_id == payload.engineer_id)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El ingeniero ya pertenece a este grupo.",
        )

    member = SupportGroupMember(**payload.model_dump())
    db.add(member)
    db.commit()
    db.refresh(member)

    return member


@router.put("/{group_id}/members/{engineer_id}", response_model=GroupMemberRead)
def update_group_member(
    group_id: int,
    engineer_id: int,
    payload: GroupMemberUpdate,
    db: Session = Depends(get_db),
):
    member = (
        db.query(SupportGroupMember)
        .filter(SupportGroupMember.support_group_id == group_id)
        .filter(SupportGroupMember.engineer_id == engineer_id)
        .first()
    )

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integrante no encontrado en este grupo.",
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(member, field, value)

    db.commit()
    db.refresh(member)

    return member


@router.delete(
    "/{group_id}/members/{engineer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_group_member(
    group_id: int,
    engineer_id: int,
    db: Session = Depends(get_db),
):
    member = (
        db.query(SupportGroupMember)
        .filter(SupportGroupMember.support_group_id == group_id)
        .filter(SupportGroupMember.engineer_id == engineer_id)
        .first()
    )

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integrante no encontrado en este grupo.",
        )

    db.delete(member)
    db.commit()

    return None