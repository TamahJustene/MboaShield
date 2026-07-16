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
    mfa_enabled: bool = False
    auth_provider: str = "local"
    must_reset_password: bool = False
    last_login_at: str | None = None


class AuthRegisterIn(BaseModel):
    display_name: str = Field(..., min_length=1)
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)


class AuthLoginIn(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=1)
    device_token: str | None = None


class LdapLoginIn(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    device_token: str | None = None


class TokenRefreshIn(BaseModel):
    refresh_token: str = Field(..., min_length=10)


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserOut
    session_id: str | None = None


class AuthSessionOut(BaseModel):
    mfa_required: bool = False
    mfa_token: str | None = None
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in_minutes: int | None = None
    user: UserOut | None = None
    session_id: str | None = None
    device_token: str | None = None
    device_id: int | None = None


class MfaCodeIn(BaseModel):
    code: str = Field(..., min_length=6, max_length=10)
    mfa_token: str | None = None
    trust_device: bool = False
    device_name: str | None = None


class MfaSetupOut(BaseModel):
    secret: str
    otpauth_uri: str
    mfa_enabled: bool = False


class OidcCallbackIn(BaseModel):
    code: str = ""
    state: str = ""
    device_token: str | None = None


class PasswordForgotIn(BaseModel):
    email: str = Field(..., min_length=3)


class PasswordResetIn(BaseModel):
    token: str = Field(..., min_length=10)
    new_password: str = Field(..., min_length=8)


class SessionRevokeIn(BaseModel):
    session_id: str | None = None
    revoke_all: bool = False
    except_session_id: str | None = None


class DeviceTrustIn(BaseModel):
    name: str = Field(default="Trusted device", min_length=1)
    fingerprint: str | None = None


class AdminUserCreateIn(BaseModel):
    display_name: str = Field(..., min_length=1)
    email: str = Field(..., min_length=3)
    role: str = "citizen"
    password: str | None = None
    must_reset_password: bool = True


class AdminUserUpdateIn(BaseModel):
    display_name: str | None = None
    role: str | None = None
    is_active: bool | None = None
    must_reset_password: bool | None = None


class OAuthClientCreateIn(BaseModel):
    name: str = Field(..., min_length=2)
    partner_org: str = Field(..., min_length=2)
    scopes: list[str] = Field(default_factory=lambda: ["checks:create", "institutions:read"])


class PartnerApiKeyIn(BaseModel):
    name: str = Field(..., min_length=2)
    partner_org: str = Field(..., min_length=2)
    scopes: list[str] = Field(default_factory=lambda: ["checks:create", "institutions:read"])
    expires_at: str | None = None


class PartnerApiKeyOut(BaseModel):
    id: int
    name: str
    partner_org: str
    key_prefix: str
    scopes: list[str]
    created_by_user_id: int | None = None
    revoked: bool = False
    expires_at: str | None = None
    last_used_at: str | None = None
    created_at: str
    api_key: str | None = None


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


class IntelligenceAnalyzeIn(BaseModel):
    text: str = ""
    name: str = ""
    handle: str = ""
    url: str = ""
    filename: str = ""
    mime_type: str = ""
    lang: str = "en"
    include_scaffolds: bool = True


class AnalysisFeedbackIn(BaseModel):
    verification_check_id: int
    label: Literal["true_positive", "false_positive", "true_negative", "false_negative"]
    note: str | None = None


class AnalysisFeedbackOut(BaseModel):
    id: int
    verification_check_id: int
    label: str
    note: str | None = None
    actor_user_id: int | None = None
    created_at: str

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


class CaseCreateIn(BaseModel):
    title: str = Field(..., min_length=3)
    summary: str | None = None
    incident_id: int | None = None
    verification_check_id: int | None = None
    institution_id: str | None = None
    region: str | None = None
    priority: str = "normal"
    assigned_to_user_id: int | None = None


class CaseUpdateIn(BaseModel):
    title: str | None = None
    summary: str | None = None
    status: str | None = None
    priority: str | None = None
    region: str | None = None
    assigned_to_user_id: int | None = None
    assignment_note: str | None = None


class CaseAssignIn(BaseModel):
    assignee_user_id: int
    note: str | None = None
    status: str | None = "investigating"


class CaseNoteIn(BaseModel):
    body: str = Field(..., min_length=2)


class IntelSourceIn(BaseModel):
    name: str = Field(..., min_length=2)
    source_class: str = Field(..., min_length=2)
    endpoint_url: str = Field(default="", min_length=0)
    tos_reference: str = Field(..., min_length=3)
    license: str = "unknown"
    auth_type: str = "none"
    credentials: dict[str, Any] | None = None
    config: dict[str, Any] | None = None
    enabled: bool = True


class IntelSourceUpdateIn(BaseModel):
    enabled: bool | None = None


class EvidenceRegisterIn(BaseModel):
    title: str = Field(..., min_length=2)
    filename: str = Field(..., min_length=1)
    content_base64: str = Field(..., min_length=4)
    content_type: str = "application/octet-stream"
    description: str | None = None
    case_id: int | None = None
    incident_id: int | None = None
    verification_check_id: int | None = None
    retention_days: int | None = Field(default=None, ge=1, le=3650)


class EvidenceTransferIn(BaseModel):
    to_user_id: int = Field(..., ge=1)
    note: str | None = None


class EvidenceRetentionIn(BaseModel):
    dry_run: bool = True


class InstitutionDomainIn(BaseModel):
    domain: str = Field(..., min_length=3)
    verification_method: str = "dns_txt"


class InstitutionDomainVerifyIn(BaseModel):
    token: str | None = None
    force: bool = False


class InstitutionMembershipIn(BaseModel):
    user_id: int | None = None
    email: str | None = None
    display_name: str | None = None
    member_role: str = "member"


class InstitutionMembershipUpdateIn(BaseModel):
    member_role: str | None = None
    status: str | None = None


class InstitutionBrandingIn(BaseModel):
    branding: dict[str, Any] | None = None
    contact_email: str | None = None


class InstitutionOfficialAccountIn(BaseModel):
    platform: str = Field(..., min_length=1)
    handle: str = Field(..., min_length=1)
    url: str | None = None
    verified: bool = True


class InstitutionApiKeyIn(BaseModel):
    name: str = Field(..., min_length=2)
    scopes: list[str] | None = None
    expires_at: str | None = None


