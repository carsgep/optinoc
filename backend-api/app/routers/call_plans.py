from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.support import CallPlanGenerateRequest, CallPlanGenerateResponse
from app.services.call_plan_service import CallPlanService

router = APIRouter(prefix="/call-plans", tags=["Call Plans"])


@router.post("/generate", response_model=CallPlanGenerateResponse)
def generate_call_plan(
    payload: CallPlanGenerateRequest,
    db: Session = Depends(get_db),
):
    service = CallPlanService(db)

    return service.generate_call_plan(
        alert_type_code=payload.alert_type_code,
        reference_date=payload.reference_date,
    )