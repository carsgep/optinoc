from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.support import Engineer, OnCallSchedule, SupportGroup
from app.schemas.support import (
    OnCallScheduleCreate,
    OnCallScheduleRead,
    OnCallScheduleUpdate,
)

router = APIRouter(prefix="/on-call-schedules", tags=["On Call Schedules"])


@router.get("/", response_model=list[OnCallScheduleRead])
def list_on_call_schedules(
    support_group_id: int | None = Query(default=None),
    active: bool | None = Query(default=True),
    db: Session = Depends(get_db),
):
    query = (
        db.query(OnCallSchedule)
        .options(
            joinedload(OnCallSchedule.engineer),
            joinedload(OnCallSchedule.support_group),
        )
    )

    if support_group_id is not None:
        query = query.filter(OnCallSchedule.support_group_id == support_group_id)

    if active is not None:
        query = query.filter(OnCallSchedule.active == active)

    return (
        query
        .order_by(
            OnCallSchedule.week_start_date.desc(),
            OnCallSchedule.support_group_id.asc(),
            OnCallSchedule.priority_order.asc(),
        )
        .all()
    )


@router.get("/current", response_model=list[OnCallScheduleRead])
def list_current_on_call_schedules(
    support_group_id: int | None = Query(default=None),
    current_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    reference_date = current_date or date.today()

    query = (
        db.query(OnCallSchedule)
        .options(
            joinedload(OnCallSchedule.engineer),
            joinedload(OnCallSchedule.support_group),
        )
        .filter(OnCallSchedule.week_start_date <= reference_date)
        .filter(OnCallSchedule.week_end_date >= reference_date)
        .filter(OnCallSchedule.active == True)
    )

    if support_group_id is not None:
        query = query.filter(OnCallSchedule.support_group_id == support_group_id)

    return (
        query
        .order_by(
            OnCallSchedule.support_group_id.asc(),
            OnCallSchedule.priority_order.asc(),
        )
        .all()
    )


@router.get("/group/{group_id}", response_model=list[OnCallScheduleRead])
def list_group_on_call_schedules(
    group_id: int,
    db: Session = Depends(get_db),
):
    group = db.query(SupportGroup).filter(SupportGroup.id == group_id).first()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo de soporte no encontrado.",
        )

    return (
        db.query(OnCallSchedule)
        .options(
            joinedload(OnCallSchedule.engineer),
            joinedload(OnCallSchedule.support_group),
        )
        .filter(OnCallSchedule.support_group_id == group_id)
        .order_by(
            OnCallSchedule.week_start_date.desc(),
            OnCallSchedule.priority_order.asc(),
        )
        .all()
    )


@router.post("/", response_model=OnCallScheduleRead, status_code=status.HTTP_201_CREATED)
def create_on_call_schedule(
    payload: OnCallScheduleCreate,
    db: Session = Depends(get_db),
):
    if payload.week_end_date < payload.week_start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha final de la semana no puede ser menor que la fecha inicial.",
        )

    group = (
        db.query(SupportGroup)
        .filter(SupportGroup.id == payload.support_group_id)
        .filter(SupportGroup.active == True)
        .first()
    )

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo de soporte no encontrado o inactivo.",
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

    existing_priority = (
        db.query(OnCallSchedule)
        .filter(OnCallSchedule.support_group_id == payload.support_group_id)
        .filter(OnCallSchedule.week_start_date == payload.week_start_date)
        .filter(OnCallSchedule.week_end_date == payload.week_end_date)
        .filter(OnCallSchedule.priority_order == payload.priority_order)
        .filter(OnCallSchedule.active == True)
        .first()
    )

    if existing_priority:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un turno activo para este grupo, semana y prioridad.",
        )

    schedule = OnCallSchedule(**payload.model_dump())
    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    schedule = (
        db.query(OnCallSchedule)
        .options(
            joinedload(OnCallSchedule.engineer),
            joinedload(OnCallSchedule.support_group),
        )
        .filter(OnCallSchedule.id == schedule.id)
        .first()
    )

    return schedule


@router.get("/{schedule_id}", response_model=OnCallScheduleRead)
def get_on_call_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
):
    schedule = (
        db.query(OnCallSchedule)
        .options(
            joinedload(OnCallSchedule.engineer),
            joinedload(OnCallSchedule.support_group),
        )
        .filter(OnCallSchedule.id == schedule_id)
        .first()
    )

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Turno no encontrado.",
        )

    return schedule


@router.put("/{schedule_id}", response_model=OnCallScheduleRead)
def update_on_call_schedule(
    schedule_id: int,
    payload: OnCallScheduleUpdate,
    db: Session = Depends(get_db),
):
    schedule = db.query(OnCallSchedule).filter(OnCallSchedule.id == schedule_id).first()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Turno no encontrado.",
        )

    update_data = payload.model_dump(exclude_unset=True)

    new_start = update_data.get("week_start_date", schedule.week_start_date)
    new_end = update_data.get("week_end_date", schedule.week_end_date)

    if new_end < new_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha final de la semana no puede ser menor que la fecha inicial.",
        )

    for field, value in update_data.items():
        setattr(schedule, field, value)

    db.commit()
    db.refresh(schedule)

    schedule = (
        db.query(OnCallSchedule)
        .options(
            joinedload(OnCallSchedule.engineer),
            joinedload(OnCallSchedule.support_group),
        )
        .filter(OnCallSchedule.id == schedule_id)
        .first()
    )

    return schedule


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_on_call_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
):
    schedule = db.query(OnCallSchedule).filter(OnCallSchedule.id == schedule_id).first()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Turno no encontrado.",
        )

    db.delete(schedule)
    db.commit()

    return None