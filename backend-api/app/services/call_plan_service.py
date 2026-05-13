from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.support import (
    AlertType,
    Engineer,
    EscalationLevel,
    EscalationPolicy,
    OnCallSchedule,
    SupportGroup,
)


class CallPlanService:
    def __init__(self, db: Session):
        self.db = db

    def generate_call_plan(
        self,
        alert_type_code: str,
        reference_date: date | None = None,
    ):
        resolved_reference_date = reference_date or date.today()
        normalized_code = alert_type_code.strip().upper()

        alert_type = (
            self.db.query(AlertType)
            .filter(AlertType.code == normalized_code)
            .filter(AlertType.active == True)
            .first()
        )

        if not alert_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No existe un tipo de alerta activo con código {normalized_code}.",
            )

        policy = (
            self.db.query(EscalationPolicy)
            .options(
                joinedload(EscalationPolicy.levels).joinedload(EscalationLevel.support_group),
                joinedload(EscalationPolicy.levels).joinedload(EscalationLevel.selected_engineer),
            )
            .filter(EscalationPolicy.alert_type_id == alert_type.id)
            .filter(EscalationPolicy.active == True)
            .first()
        )

        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No existe una política activa para la alerta {normalized_code}.",
            )

        active_levels = sorted(
            [level for level in policy.levels if level.active],
            key=lambda item: item.level_order,
        )

        if not active_levels:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La política no tiene niveles de escalamiento activos.",
            )

        steps = []

        for level in active_levels:
            engineer = self._resolve_engineer(level, resolved_reference_date)

            if not engineer:
                continue

            support_group = (
                level.support_group
                or self.db.query(SupportGroup)
                .filter(SupportGroup.id == level.support_group_id)
                .first()
            )

            if level.call_extension and engineer.extension:
                steps.append(
                    self._build_step(
                        level=level,
                        support_group=support_group,
                        engineer=engineer,
                        destination_type="EXTENSION",
                        destination_value=engineer.extension,
                        retry_attempts=policy.retry_attempts,
                        retry_interval_seconds=policy.retry_interval_seconds,
                    )
                )

            if level.call_mobile and engineer.mobile_phone:
                steps.append(
                    self._build_step(
                        level=level,
                        support_group=support_group,
                        engineer=engineer,
                        destination_type="MOBILE",
                        destination_value=engineer.mobile_phone,
                        retry_attempts=policy.retry_attempts,
                        retry_interval_seconds=policy.retry_interval_seconds,
                    )
                )

        if not steps:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se pudo construir un plan de llamadas. Revisa turnos, ingenieros, extensiones o celulares.",
            )

        return {
            "alert_type_code": normalized_code,
            "policy_id": policy.id,
            "policy_name": policy.name,
            "reference_date": resolved_reference_date,
            "steps": steps,
        }

    def _resolve_engineer(
        self,
        level: EscalationLevel,
        reference_date: date,
    ) -> Engineer | None:
        if level.use_on_call_schedule:
            if level.on_call_priority_order is None:
                return None

            schedule = (
                self.db.query(OnCallSchedule)
                .options(joinedload(OnCallSchedule.engineer))
                .filter(OnCallSchedule.support_group_id == level.support_group_id)
                .filter(OnCallSchedule.priority_order == level.on_call_priority_order)
                .filter(OnCallSchedule.week_start_date <= reference_date)
                .filter(OnCallSchedule.week_end_date >= reference_date)
                .filter(OnCallSchedule.active == True)
                .first()
            )

            if not schedule:
                return None

            return schedule.engineer

        if level.selected_engineer_id:
            return (
                level.selected_engineer
                or self.db.query(Engineer)
                .filter(Engineer.id == level.selected_engineer_id)
                .filter(Engineer.active == True)
                .first()
            )

        return None

    def _build_step(
        self,
        level: EscalationLevel,
        support_group: SupportGroup,
        engineer: Engineer,
        destination_type: str,
        destination_value: str,
        retry_attempts: int,
        retry_interval_seconds: int,
    ):
        return {
            "level": level.level_order,
            "support_group_id": support_group.id,
            "support_group_name": support_group.name,
            "engineer_id": engineer.id,
            "engineer_name": engineer.full_name,
            "destination_type": destination_type,
            "destination_value": destination_value,
            "retry_attempts": retry_attempts,
            "retry_interval_seconds": retry_interval_seconds,
            "call_extension": level.call_extension,
            "call_mobile": level.call_mobile,
        }