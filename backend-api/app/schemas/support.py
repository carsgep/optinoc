from datetime import datetime
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