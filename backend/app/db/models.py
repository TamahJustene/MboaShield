from __future__ import annotations

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    role: Mapped[str] = mapped_column(String(64), nullable=False, default="citizen")
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    failed_login_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)


class Institution(Base):
    __tablename__ = "institutions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_name: Mapped[str] = mapped_column(String(128), nullable=False)
    website_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    verified: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    handles_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)


class VerificationCheck(Base):
    __tablename__ = "verification_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    check_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    input_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_handle: Mapped[str | None] = mapped_column(String(255), nullable=True)
    input_filename: Mapped[str | None] = mapped_column(String(512), nullable=True)
    input_lang: Mapped[str] = mapped_column(String(16), nullable=False, default="en")
    risk_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_band: Mapped[str | None] = mapped_column(String(32), nullable=True)
    result_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    signals: Mapped[list["VerificationSignal"]] = relationship(back_populates="check")


class VerificationSignal(Base):
    __tablename__ = "verification_signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    verification_check_id: Mapped[int] = mapped_column(ForeignKey("verification_checks.id"), nullable=False)
    signal_type: Mapped[str] = mapped_column(String(64), nullable=False)
    signal_label: Mapped[str] = mapped_column(Text, nullable=False)
    signal_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)

    check: Mapped[VerificationCheck] = relationship(back_populates="signals")


class LessonCertificate(Base):
    __tablename__ = "lesson_certificates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    certificate_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    learner_name: Mapped[str] = mapped_column(String(255), nullable=False)
    lesson_id: Mapped[str] = mapped_column(String(64), nullable=False)
    lesson_title_en: Mapped[str] = mapped_column(String(255), nullable=False)
    lesson_title_fr: Mapped[str] = mapped_column(String(255), nullable=False)
    issued_on: Mapped[str] = mapped_column(String(32), nullable=False)
    issuer: Mapped[str] = mapped_column(String(255), nullable=False)
    founder: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)


class IncidentReport(Base):
    __tablename__ = "incident_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    verification_check_id: Mapped[int | None] = mapped_column(ForeignKey("verification_checks.id"), nullable=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    report_type: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open", index=True)
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(32), nullable=False, default="normal")
    region: Mapped[str | None] = mapped_column(String(128), nullable=True)
    assigned_to_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    institution_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("institutions.id"), nullable=True)
    decision_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    public_advisory: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_summary_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(64), nullable=False)


class IncidentEvent(Base):
    __tablename__ = "incident_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incident_reports.id"), nullable=False, index=True)
    from_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actor_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False, index=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actor_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False, default="success")
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False, index=True)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = (UniqueConstraint("token_hash", name="uq_refresh_token_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[str] = mapped_column(String(64), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
