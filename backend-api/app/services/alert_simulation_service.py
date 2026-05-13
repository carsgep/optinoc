from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.support import AlertEvent, AlertType, CallAttempt
from app.schemas.support import AlertSimulationRequest
from app.services.call_plan_service import CallPlanService


HUMAN_ANSWER_STATUS = "ANSWERED_HUMAN"

RETRYABLE_STATUSES = {
    "NO_ANSWER",
    "VOICEMAIL",
    "BUSY",
    "FAILED",
}


class AlertSimulationService:
    def __init__(self, db: Session):
        self.db = db

    def simulate_alert_flow(self, payload: AlertSimulationRequest):
        normalized_code = payload.alert_type_code.strip().upper()

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

        call_plan_service = CallPlanService(self.db)
        call_plan = call_plan_service.generate_call_plan(
            alert_type_code=normalized_code,
            reference_date=payload.reference_date,
        )

        retry_interval_minutes = self._resolve_retry_interval_minutes(
            payload=payload,
            call_plan=call_plan,
        )

        outcomes_by_key = self._build_outcomes_map(payload)

        alert_event = AlertEvent(
            alert_type_id=alert_type.id,
            title=payload.title,
            message=payload.message,
            status="CALLING",
        )

        self.db.add(alert_event)
        self.db.commit()
        self.db.refresh(alert_event)

        attempts_response = []
        simulation_start = datetime.now()

        final_status = "NO_ANSWER"
        answered_by = None
        answered_level = None

        current_time = simulation_start

        for step in call_plan["steps"]:
            level = step["level"]

            for attempt_number in range(1, step["retry_attempts"] + 1):
                simulated_status = self._get_simulated_status(
                    outcomes_by_key=outcomes_by_key,
                    level=level,
                    attempt_number=attempt_number,
                )

                counts_as_answer = simulated_status == HUMAN_ANSWER_STATUS

                call_attempt = CallAttempt(
                    alert_event_id=alert_event.id,
                    escalation_level_id=None,
                    engineer_id=step["engineer_id"],
                    attempt_number=attempt_number,
                    destination_type=step["destination_type"],
                    destination_value=step["destination_value"],
                    call_status=simulated_status,
                    call_id=f"SIM-{alert_event.id}-{level}-{attempt_number}",
                    started_at=current_time,
                    ended_at=current_time + timedelta(seconds=15),
                )

                self.db.add(call_attempt)

                attempts_response.append(
                    {
                        "level": level,
                        "engineer_id": step["engineer_id"],
                        "engineer_name": step["engineer_name"],
                        "destination_type": step["destination_type"],
                        "destination_value": step["destination_value"],
                        "attempt_number": attempt_number,
                        "scheduled_at": current_time,
                        "simulated_status": simulated_status,
                        "counts_as_answer": counts_as_answer,
                    }
                )

                if counts_as_answer:
                    final_status = "ANSWERED"
                    answered_by = step["engineer_name"]
                    answered_level = level
                    alert_event.status = "ANSWERED"
                    alert_event.resolved_at = current_time + timedelta(seconds=15)

                    self.db.commit()

                    return {
                        "alert_event_id": alert_event.id,
                        "alert_type_code": normalized_code,
                        "title": payload.title,
                        "message": payload.message,
                        "final_status": final_status,
                        "answered_by": answered_by,
                        "answered_level": answered_level,
                        "retry_interval_minutes_used": retry_interval_minutes,
                        "attempts": attempts_response,
                    }

                # VOICEMAIL no cuenta como contestación válida.
                # En una integración real, aquí OPTI/Drachtio colgaría la llamada
                # y programaría el siguiente intento después del intervalo definido.
                current_time = current_time + timedelta(minutes=retry_interval_minutes)

        alert_event.status = "FAILED"
        self.db.commit()

        return {
            "alert_event_id": alert_event.id,
            "alert_type_code": normalized_code,
            "title": payload.title,
            "message": payload.message,
            "final_status": final_status,
            "answered_by": answered_by,
            "answered_level": answered_level,
            "retry_interval_minutes_used": retry_interval_minutes,
            "attempts": attempts_response,
        }

    def _resolve_retry_interval_minutes(
        self,
        payload: AlertSimulationRequest,
        call_plan: dict,
    ) -> int:
        if payload.retry_interval_minutes is not None:
            return payload.retry_interval_minutes

        if call_plan["steps"]:
            seconds = call_plan["steps"][0]["retry_interval_seconds"]
            return max(1, int(seconds / 60))

        return 2

    def _build_outcomes_map(self, payload: AlertSimulationRequest):
        valid_statuses = RETRYABLE_STATUSES.union({HUMAN_ANSWER_STATUS})
        outcomes_by_key = {}

        for outcome in payload.simulated_outcomes:
            normalized_status = outcome.status.strip().upper()

            if normalized_status not in valid_statuses:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Estado simulado no válido: {outcome.status}. "
                        "Usa ANSWERED_HUMAN, VOICEMAIL, NO_ANSWER, BUSY o FAILED."
                    ),
                )

            outcomes_by_key[(outcome.level, outcome.attempt_number)] = normalized_status

        return outcomes_by_key

    def _get_simulated_status(
        self,
        outcomes_by_key: dict,
        level: int,
        attempt_number: int,
    ) -> str:
        return outcomes_by_key.get((level, attempt_number), "NO_ANSWER")