from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

CheckType = Literal["text", "impersonation", "audio", "media"]
RiskBand = Literal["low", "medium", "high"]


class TextIn(BaseModel):
    text: str = Field(..., min_length=1)
    lang: str = "en"


class ImpersonationIn(BaseModel):
    name: str = ""
    handle: str = ""
    lang: str = "en"


class CompleteIn(BaseModel):
    lesson_id: str
    learner_name: str = "Citizen"


class CheckInputMeta(BaseModel):
    text: str | None = None
    handle: str | None = None
    filename: str | None = None
    lang: str = "en"


class VerificationSignalOut(BaseModel):
    signal_type: str
    signal_label: str
    signal_score: int | None = None


class StoredCheckOut(BaseModel):
    id: int
    check_type: str
    input: CheckInputMeta
    risk_score: int | None = None
    risk_band: str | None = None
    result: dict[str, Any]
    signals: list[VerificationSignalOut] = Field(default_factory=list)
    created_at: str


class RecentChecksOut(BaseModel):
    checks: list[StoredCheckOut]
    count: int


class CertificateOut(BaseModel):
    id: int
    certificate_id: str
    learner_name: str
    lesson_id: str
    lesson_title_en: str
    lesson_title_fr: str
    issued_on: str
    issuer: str
    founder: str
    created_at: str


class RecentCertificatesOut(BaseModel):
    certificates: list[CertificateOut]
    count: int


class UserIn(BaseModel):
    display_name: str = Field(..., min_length=1)
    email: str | None = None


class UserOut(BaseModel):
    id: int
    display_name: str
    email: str | None = None
    role: str
    created_at: str
    is_active: bool = True


class AuthRegisterIn(BaseModel):
    display_name: str = Field(..., min_length=1)
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)


class AuthLoginIn(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=1)


class TokenRefreshIn(BaseModel):
    refresh_token: str = Field(..., min_length=10)


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserOut


class InstitutionOut(BaseModel):
    id: str
    name: str
    short_name: str
    url: str | None = None
    verified: bool = True
    handles: list[str] = Field(default_factory=list)
    created_at: str | None = None


class InstitutionsOut(BaseModel):
    institutions: list[InstitutionOut]
    count: int


class CaseAnalyzeIn(BaseModel):
    text: str = ""
    name: str = ""
    handle: str = ""
    lang: str = "en"

ReportType = Literal[
    "disinformation",
    "impersonation",
    "voice_clone",
    "synthetic_media",
    "scam",
    "other",
]
ReportStatus = Literal[
    "open",
    "ai_analysis",
    "analyst_review",
    "reviewing",
    "institution_review",
    "decision",
    "public_advisory",
    "resolved",
    "archived",
    "dismissed",
]


class IncidentReportIn(BaseModel):
    report_type: ReportType
    description: str = Field(..., min_length=8)
    verification_check_id: int | None = None
    region: str | None = None
    priority: str = "normal"
    institution_id: str | None = None


class IncidentStatusIn(BaseModel):
    status: ReportStatus
    reviewer_note: str | None = None
    decision_summary: str | None = None
    public_advisory: str | None = None
    assigned_to_user_id: int | None = None
    institution_id: str | None = None
    region: str | None = None
    priority: str | None = None


class IncidentTransitionIn(BaseModel):
    to_status: ReportStatus
    note: str | None = None
    decision_summary: str | None = None
    public_advisory: str | None = None
    assigned_to_user_id: int | None = None
    institution_id: str | None = None
    region: str | None = None
    priority: str | None = None


class IncidentReportOut(BaseModel):
    id: int
    verification_check_id: int | None = None
    user_id: int | None = None
    report_type: str
    description: str
    status: str
    reviewer_note: str | None = None
    priority: str = "normal"
    region: str | None = None
    assigned_to_user_id: int | None = None
    institution_id: str | None = None
    decision_summary: str | None = None
    public_advisory: str | None = None
    ai_summary: dict[str, Any] | None = None
    next_actions: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str


class IncidentReportsOut(BaseModel):
    reports: list[IncidentReportOut]
    count: int


class IncidentEventOut(BaseModel):
    id: int
    incident_id: int
    from_status: str | None = None
    to_status: str
    actor_user_id: int | None = None
    actor_role: str | None = None
    note: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: str


class IncidentTimelineOut(BaseModel):
    incident_id: int
    events: list[IncidentEventOut]
    count: int


class InstitutionIn(BaseModel):
    id: str = Field(..., min_length=2)
    name: str = Field(..., min_length=2)
    short_name: str = Field(..., min_length=2)
    url: str | None = None
    verified: bool = True
    handles: list[str] = Field(default_factory=list)


class InstitutionUpdateIn(BaseModel):
    name: str | None = None
    short_name: str | None = None
    url: str | None = None
    verified: bool | None = None
    handles: list[str] | None = None
