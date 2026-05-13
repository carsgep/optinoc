from fastapi import FastAPI

from app.config import settings
from app.database import Base, engine
from app.routers import (
    alert_types,
    call_plans,
    engineers,
    escalation_policies,
    on_call_schedules,
    support_groups,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
    }


app.include_router(support_groups.router)
app.include_router(engineers.router)
app.include_router(on_call_schedules.router)
app.include_router(alert_types.router)
app.include_router(escalation_policies.router)
app.include_router(call_plans.router)