from datetime import date
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SupportGroupBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    is_director_group: bool = False
    active: bool = True


class SupportGroupCreate(SupportGroupBase):
    pass


class SupportGroupUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    description: Optional[str] = None
    is_director_group: Optional[bool] = None
    active: Optional[bool] = None


class SupportGroupRead(SupportGroupBase):
    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class EngineerBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150)
    email: Optional[str] = None
    extension: Optional[str] = None
    mobile_phone: Optional[str] = None
    active: bool = True


class EngineerCreate(EngineerBase):
    pass


class EngineerUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    email: Optional[str] = None
    extension: Optional[str] = None
    mobile_phone: Optional[str] = None
    active: Optional[bool] = None


class EngineerRead(EngineerBase):
    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class GroupMemberCreate(BaseModel):
    support_group_id: int
    engineer_id: int
    role: Optional[str] = None
    active: bool = True


class GroupMemberRead(BaseModel):
    id: int
    support_group_id: int
    engineer_id: int
    role: Optional[str] = None
    active: bool = True
    engineer: EngineerRead

    model_config = ConfigDict(from_attributes=True)


class GroupMemberUpdate(BaseModel):
    role: Optional[str] = None
    active: Optional[bool] = None

class OnCallScheduleBase(BaseModel):
    support_group_id: int
    engineer_id: int
    week_start_date: date
    week_end_date: date
    priority_order: int = Field(default=1, ge=1)
    active: bool = True


class OnCallScheduleCreate(OnCallScheduleBase):
    pass


class OnCallScheduleUpdate(BaseModel):
    support_group_id: Optional[int] = None
    engineer_id: Optional[int] = None
    week_start_date: Optional[date] = None
    week_end_date: Optional[date] = None
    priority_order: Optional[int] = Field(default=None, ge=1)
    active: Optional[bool] = None


class OnCallScheduleRead(OnCallScheduleBase):
    id: int
    created_at: Optional[datetime] = None
    engineer: Optional[EngineerRead] = None
    support_group: Optional[SupportGroupRead] = None

    model_config = ConfigDict(from_attributes=True)

class AlertTypeBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=100)
    name: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = None
    severity: Optional[str] = None
    active: bool = True


class AlertTypeCreate(AlertTypeBase):
    pass


class AlertTypeUpdate(BaseModel):
    code: Optional[str] = Field(default=None, min_length=2, max_length=100)
    name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    description: Optional[str] = None
    severity: Optional[str] = None
    active: Optional[bool] = None


class AlertTypeRead(AlertTypeBase):
    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class EscalationLevelBase(BaseModel):
    level_order: int = Field(..., ge=1)
    support_group_id: int
    selected_engineer_id: Optional[int] = None
    use_on_call_schedule: bool = True
    on_call_priority_order: Optional[int] = Field(default=None, ge=1)
    call_extension: bool = True
    call_mobile: bool = False
    active: bool = True


class EscalationLevelCreate(EscalationLevelBase):
    pass


class EscalationLevelUpdate(BaseModel):
    level_order: Optional[int] = Field(default=None, ge=1)
    support_group_id: Optional[int] = None
    selected_engineer_id: Optional[int] = None
    use_on_call_schedule: Optional[bool] = None
    on_call_priority_order: Optional[int] = Field(default=None, ge=1)
    call_extension: Optional[bool] = None
    call_mobile: Optional[bool] = None
    active: Optional[bool] = None


class EscalationLevelRead(EscalationLevelBase):
    id: int
    escalation_policy_id: int
    support_group: Optional[SupportGroupRead] = None
    selected_engineer: Optional[EngineerRead] = None

    model_config = ConfigDict(from_attributes=True)


class EscalationPolicyBase(BaseModel):
    alert_type_id: int
    name: str = Field(..., min_length=2, max_length=150)
    retry_attempts: int = Field(default=3, ge=1)
    retry_interval_seconds: int = Field(default=120, ge=1)
    active: bool = True


class EscalationPolicyCreate(EscalationPolicyBase):
    pass


class EscalationPolicyUpdate(BaseModel):
    alert_type_id: Optional[int] = None
    name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    retry_attempts: Optional[int] = Field(default=None, ge=1)
    retry_interval_seconds: Optional[int] = Field(default=None, ge=1)
    active: Optional[bool] = None


class EscalationPolicyRead(EscalationPolicyBase):
    id: int
    created_at: Optional[datetime] = None
    alert_type: Optional[AlertTypeRead] = None
    levels: list[EscalationLevelRead] = []

    model_config = ConfigDict(from_attributes=True)