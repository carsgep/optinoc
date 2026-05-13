from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class SupportGroup(Base):
    __tablename__ = "support_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text)
    is_director_group = Column(Boolean, default=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    members = relationship("SupportGroupMember", back_populates="support_group")


class Engineer(Base):
    __tablename__ = "engineers"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False, index=True)
    email = Column(String(150))
    extension = Column(String(20))
    mobile_phone = Column(String(30))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    groups = relationship("SupportGroupMember", back_populates="engineer")


class SupportGroupMember(Base):
    __tablename__ = "support_group_members"

    id = Column(Integer, primary_key=True, index=True)
    support_group_id = Column(Integer, ForeignKey("support_groups.id"), nullable=False)
    engineer_id = Column(Integer, ForeignKey("engineers.id"), nullable=False)
    role = Column(String(50))
    active = Column(Boolean, default=True)

    support_group = relationship("SupportGroup", back_populates="members")
    engineer = relationship("Engineer", back_populates="groups")

    __table_args__ = (
        UniqueConstraint("support_group_id", "engineer_id", name="uq_group_engineer"),
    )

class AlertType(Base):
    __tablename__ = "alert_types"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), nullable=False, unique=True, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text)
    severity = Column(String(50))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    policies = relationship("EscalationPolicy", back_populates="alert_type")

class EscalationPolicy(Base):
    __tablename__ = "escalation_policies"

    id = Column(Integer, primary_key=True, index=True)
    alert_type_id = Column(Integer, ForeignKey("alert_types.id"), nullable=False)
    name = Column(String(150), nullable=False)
    retry_attempts = Column(Integer, default=3)
    retry_interval_seconds = Column(Integer, default=120)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    alert_type = relationship("AlertType", back_populates="policies")
    levels = relationship("EscalationLevel", back_populates="policy")


class EscalationLevel(Base):
    __tablename__ = "escalation_levels"

    id = Column(Integer, primary_key=True, index=True)
    escalation_policy_id = Column(Integer, ForeignKey("escalation_policies.id"), nullable=False)
    level_order = Column(Integer, nullable=False)
    support_group_id = Column(Integer, ForeignKey("support_groups.id"), nullable=False)
    selected_engineer_id = Column(Integer, ForeignKey("engineers.id"))
    use_on_call_schedule = Column(Boolean, default=True)
    on_call_priority_order = Column(Integer)
    call_extension = Column(Boolean, default=True)
    call_mobile = Column(Boolean, default=False)
    active = Column(Boolean, default=True)

    policy = relationship("EscalationPolicy", back_populates="levels")
    support_group = relationship("SupportGroup")
    selected_engineer = relationship("Engineer")

    __table_args__ = (
        UniqueConstraint("escalation_policy_id", "level_order", name="uq_policy_level"),
    )

class OnCallSchedule(Base):
    __tablename__ = "on_call_schedules"

    id = Column(Integer, primary_key=True, index=True)
    support_group_id = Column(Integer, ForeignKey("support_groups.id"), nullable=False)
    engineer_id = Column(Integer, ForeignKey("engineers.id"), nullable=False)
    week_start_date = Column(Date, nullable=False)
    week_end_date = Column(Date, nullable=False)
    priority_order = Column(Integer, default=1)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    support_group = relationship("SupportGroup")
    engineer = relationship("Engineer")

class AlertEvent(Base):
    __tablename__ = "alert_events"

    id = Column(Integer, primary_key=True, index=True)
    alert_type_id = Column(Integer, ForeignKey("alert_types.id"), nullable=False)
    title = Column(String(200))
    message = Column(Text, nullable=False)
    status = Column(String(50), default="PENDING")
    created_at = Column(DateTime, server_default=func.now())
    resolved_at = Column(DateTime)


class CallAttempt(Base):
    __tablename__ = "call_attempts"

    id = Column(Integer, primary_key=True, index=True)
    alert_event_id = Column(Integer, ForeignKey("alert_events.id"), nullable=False)
    escalation_level_id = Column(Integer, ForeignKey("escalation_levels.id"))
    engineer_id = Column(Integer, ForeignKey("engineers.id"))
    attempt_number = Column(Integer, nullable=False)
    destination_type = Column(String(30))
    destination_value = Column(String(50))
    call_status = Column(String(50))
    call_id = Column(String(150))
    started_at = Column(DateTime, server_default=func.now())
    ended_at = Column(DateTime)