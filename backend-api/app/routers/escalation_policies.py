from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.support import (
    AlertType,
    Engineer,
    EscalationLevel,
    EscalationPolicy,
    SupportGroup,
)
from app.schemas.support import (
    EscalationLevelCreate,
    EscalationLevelRead,
    EscalationLevelUpdate,
    EscalationPolicyCreate,
    EscalationPolicyRead,
    EscalationPolicyUpdate,
)

router = APIRouter(prefix="/escalation-policies", tags=["Escalation Policies"])


@router.get("/", response_model=list[EscalationPolicyRead])
def list_escalation_policies(db: Session = Depends(get_db)):
    return (
        db.query(EscalationPolicy)
        .options(
            joinedload(EscalationPolicy.alert_type),
            joinedload(EscalationPolicy.levels).joinedload(EscalationLevel.support_group),
            joinedload(EscalationPolicy.levels).joinedload(EscalationLevel.selected_engineer),
        )
        .order_by(EscalationPolicy.id.asc())
        .all()
    )


@router.post("/", response_model=EscalationPolicyRead, status_code=status.HTTP_201_CREATED)
def create_escalation_policy(
    payload: EscalationPolicyCreate,
    db: Session = Depends(get_db),
):
    alert_type = (
        db.query(AlertType)
        .filter(AlertType.id == payload.alert_type_id)
        .filter(AlertType.active == True)
        .first()
    )

    if not alert_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de alerta no encontrado o inactivo.",
        )

    existing = (
        db.query(EscalationPolicy)
        .filter(EscalationPolicy.alert_type_id == payload.alert_type_id)
        .filter(EscalationPolicy.active == True)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una política activa para este tipo de alerta.",
        )

    policy = EscalationPolicy(**payload.model_dump())
    db.add(policy)
    db.commit()
    db.refresh(policy)

    return (
        db.query(EscalationPolicy)
        .options(joinedload(EscalationPolicy.alert_type))
        .filter(EscalationPolicy.id == policy.id)
        .first()
    )


@router.get("/{policy_id}", response_model=EscalationPolicyRead)
def get_escalation_policy(policy_id: int, db: Session = Depends(get_db)):
    policy = (
        db.query(EscalationPolicy)
        .options(
            joinedload(EscalationPolicy.alert_type),
            joinedload(EscalationPolicy.levels).joinedload(EscalationLevel.support_group),
            joinedload(EscalationPolicy.levels).joinedload(EscalationLevel.selected_engineer),
        )
        .filter(EscalationPolicy.id == policy_id)
        .first()
    )

    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Política de escalamiento no encontrada.",
        )

    return policy


@router.put("/{policy_id}", response_model=EscalationPolicyRead)
def update_escalation_policy(
    policy_id: int,
    payload: EscalationPolicyUpdate,
    db: Session = Depends(get_db),
):
    policy = db.query(EscalationPolicy).filter(EscalationPolicy.id == policy_id).first()

    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Política de escalamiento no encontrada.",
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(policy, field, value)

    db.commit()
    db.refresh(policy)

    return (
        db.query(EscalationPolicy)
        .options(
            joinedload(EscalationPolicy.alert_type),
            joinedload(EscalationPolicy.levels).joinedload(EscalationLevel.support_group),
            joinedload(EscalationPolicy.levels).joinedload(EscalationLevel.selected_engineer),
        )
        .filter(EscalationPolicy.id == policy_id)
        .first()
    )


@router.post(
    "/{policy_id}/levels",
    response_model=EscalationLevelRead,
    status_code=status.HTTP_201_CREATED,
)
def add_escalation_level(
    policy_id: int,
    payload: EscalationLevelCreate,
    db: Session = Depends(get_db),
):
    policy = (
        db.query(EscalationPolicy)
        .filter(EscalationPolicy.id == policy_id)
        .filter(EscalationPolicy.active == True)
        .first()
    )

    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Política de escalamiento no encontrada o inactiva.",
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

    if payload.selected_engineer_id:
        engineer = (
            db.query(Engineer)
            .filter(Engineer.id == payload.selected_engineer_id)
            .filter(Engineer.active == True)
            .first()
        )

        if not engineer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ingeniero seleccionado no encontrado o inactivo.",
            )

    if payload.use_on_call_schedule and payload.on_call_priority_order is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Si use_on_call_schedule es true, debes enviar on_call_priority_order.",
        )

    if not payload.use_on_call_schedule and payload.selected_engineer_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Si no usas turno semanal, debes seleccionar un ingeniero específico.",
        )

    existing_level = (
        db.query(EscalationLevel)
        .filter(EscalationLevel.escalation_policy_id == policy_id)
        .filter(EscalationLevel.level_order == payload.level_order)
        .first()
    )

    if existing_level:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un nivel con ese orden para esta política.",
        )

    level = EscalationLevel(
        escalation_policy_id=policy_id,
        **payload.model_dump(),
    )

    db.add(level)
    db.commit()
    db.refresh(level)

    return (
        db.query(EscalationLevel)
        .options(
            joinedload(EscalationLevel.support_group),
            joinedload(EscalationLevel.selected_engineer),
        )
        .filter(EscalationLevel.id == level.id)
        .first()
    )


@router.put("/{policy_id}/levels/{level_id}", response_model=EscalationLevelRead)
def update_escalation_level(
    policy_id: int,
    level_id: int,
    payload: EscalationLevelUpdate,
    db: Session = Depends(get_db),
):
    level = (
        db.query(EscalationLevel)
        .filter(EscalationLevel.id == level_id)
        .filter(EscalationLevel.escalation_policy_id == policy_id)
        .first()
    )

    if not level:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nivel de escalamiento no encontrado.",
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(level, field, value)

    if level.use_on_call_schedule and level.on_call_priority_order is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Si use_on_call_schedule es true, debes tener on_call_priority_order.",
        )

    if not level.use_on_call_schedule and level.selected_engineer_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Si no usas turno semanal, debes seleccionar un ingeniero específico.",
        )

    db.commit()
    db.refresh(level)

    return (
        db.query(EscalationLevel)
        .options(
            joinedload(EscalationLevel.support_group),
            joinedload(EscalationLevel.selected_engineer),
        )
        .filter(EscalationLevel.id == level_id)
        .first()
    )


@router.delete("/{policy_id}/levels/{level_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_escalation_level(
    policy_id: int,
    level_id: int,
    db: Session = Depends(get_db),
):
    level = (
        db.query(EscalationLevel)
        .filter(EscalationLevel.id == level_id)
        .filter(EscalationLevel.escalation_policy_id == policy_id)
        .first()
    )

    if not level:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nivel de escalamiento no encontrado.",
        )

    db.delete(level)
    db.commit()

    return None