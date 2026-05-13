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