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


ReportType = Literal[
    "disinformation",
    "impersonation",
    "voice_clone",
    "synthetic_media",
    "scam",
    "other",
]
ReportStatus = Literal["open", "reviewing", "resolved", "dismissed"]


class IncidentReportIn(BaseModel):
    report_type: ReportType
    description: str = Field(..., min_length=8)
    verification_check_id: int | None = None


class IncidentStatusIn(BaseModel):
    status: ReportStatus
    reviewer_note: str | None = None


class IncidentReportOut(BaseModel):
    id: int
    verification_check_id: int | None = None
    user_id: int | None = None
    report_type: str
    description: str
    status: str
    reviewer_note: str | None = None
    created_at: str
    updated_at: str


class IncidentReportsOut(BaseModel):
    reports: list[IncidentReportOut]
    count: int
