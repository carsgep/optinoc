from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.support import AlertSimulationRequest, AlertSimulationResponse
from app.services.alert_simulation_service import AlertSimulationService

router = APIRouter(prefix="/alert-events", tags=["Alert Events"])


@router.post("/simulate", response_model=AlertSimulationResponse)
def simulate_alert_event(
    payload: AlertSimulationRequest,
    db: Session = Depends(get_db),
):
    service = AlertSimulationService(db)
    return service.simulate_alert_flow(payload)