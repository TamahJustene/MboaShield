# OpenAPI path summary

**Title:** MboaShield API
**Version:** 1.9.0

| Method | Path | Summary |
|---|---|---|
| GET | `/` | Index |
| GET | `/api/v1/admin/users` | Admin List Users |
| POST | `/api/v1/admin/users` | Admin Create |
| GET | `/api/v1/admin/users/{user_id}` | Admin Get User |
| PATCH | `/api/v1/admin/users/{user_id}` | Admin Patch User |
| GET | `/api/v1/ai-platform/calibration` | Api Calibration |
| GET | `/api/v1/ai-platform/evaluation/latest` | Api Latest Evaluation |
| POST | `/api/v1/ai-platform/evaluation/run` | Api Run Evaluation |
| GET | `/api/v1/ai-platform/health` | Api Ai Health |
| GET | `/api/v1/ai-platform/models` | Api List Models |
| POST | `/api/v1/ai-platform/models` | Api Register Model |
| GET | `/api/v1/ai-platform/models/{model_id}/verify-checksum` | Api Verify Checksum |
| GET | `/api/v1/ai-platform/monitoring` | Api Monitoring |
| POST | `/api/v1/ambassadors/complete` | Api Complete |
| GET | `/api/v1/ambassadors/lessons` | Api Lessons |
| GET | `/api/v1/analyst/queue` | Api Analyst Queue |
| GET | `/api/v1/analyst/summary` | Api Analyst Summary |
| POST | `/api/v1/analytics/feedback` | Api Analysis Feedback |
| GET | `/api/v1/analytics/incidents/timeline` | Api Incident Timeline Analytics |
| GET | `/api/v1/analytics/national` | Api National Analytics |
| GET | `/api/v1/analytics/participation` | Api Participation Analytics |
| GET | `/api/v1/analytics/performance` | Api Performance Analytics |
| GET | `/api/v1/analytics/regions` | Api Regional Analytics |
| GET | `/api/v1/analytics/threats` | Api Threat Analytics |
| POST | `/api/v1/analyze` | Api Analyze Case |
| GET | `/api/v1/announcements` | Api List |
| POST | `/api/v1/announcements` | Api Create |
| GET | `/api/v1/announcements/health` | Api Comms Health |
| GET | `/api/v1/announcements/{announcement_id}` | Api Get |
| PATCH | `/api/v1/announcements/{announcement_id}` | Api Update |
| GET | `/api/v1/announcements/{announcement_id}/certificate` | Api Certificate |
| POST | `/api/v1/announcements/{announcement_id}/publish` | Api Publish |
| GET | `/api/v1/announcements/{announcement_id}/qr` | Api Qr |
| POST | `/api/v1/announcements/{announcement_id}/revoke` | Api Revoke |
| GET | `/api/v1/announcements/{announcement_id}/verify` | Api Verify Managed |
| GET | `/api/v1/audit/logs` | Api Audit Logs |
| GET | `/api/v1/auth/devices` | Devices |
| POST | `/api/v1/auth/devices/trust` | Devices Trust |
| DELETE | `/api/v1/auth/devices/{device_id}` | Devices Revoke |
| POST | `/api/v1/auth/ldap/login` | Ldap Login |
| POST | `/api/v1/auth/login` | Login |
| POST | `/api/v1/auth/logout` | Logout |
| GET | `/api/v1/auth/me` | Me |
| POST | `/api/v1/auth/mfa/disable` | Mfa Disable |
| POST | `/api/v1/auth/mfa/enable` | Mfa Enable |
| POST | `/api/v1/auth/mfa/setup` | Mfa Setup |
| POST | `/api/v1/auth/mfa/verify` | Mfa Verify |
| GET | `/api/v1/auth/oidc/providers` | List Oidc Providers |
| GET | `/api/v1/auth/oidc/{provider_id}/authorize` | Oidc Authorize |
| POST | `/api/v1/auth/oidc/{provider_id}/callback` | Oidc Callback |
| POST | `/api/v1/auth/password/forgot` | Password Forgot |
| POST | `/api/v1/auth/password/reset` | Password Reset |
| POST | `/api/v1/auth/refresh` | Refresh |
| POST | `/api/v1/auth/register` | Register |
| POST | `/api/v1/auth/saml/acs` | Saml Acs |
| GET | `/api/v1/auth/saml/metadata` | Saml Metadata |
| GET | `/api/v1/auth/security-status` | Security Status |
| GET | `/api/v1/auth/sessions` | Sessions |
| POST | `/api/v1/auth/sessions/revoke` | Sessions Revoke |
| GET | `/api/v1/cases` | Api List Cases |
| POST | `/api/v1/cases` | Api Create Case |
| GET | `/api/v1/cases/{case_id}` | Api Get Case |
| PATCH | `/api/v1/cases/{case_id}` | Api Patch Case |
| POST | `/api/v1/cases/{case_id}/assign` | Api Assign Case |
| GET | `/api/v1/cases/{case_id}/assignments` | Api Assignments |
| GET | `/api/v1/cases/{case_id}/evidence` | Api Evidence |
| GET | `/api/v1/cases/{case_id}/notes` | Api List Notes |
| POST | `/api/v1/cases/{case_id}/notes` | Api Add Note |
| GET | `/api/v1/cases/{case_id}/workspace` | Api Workspace |
| GET | `/api/v1/certificates/recent` | Api Recent Certificates |
| GET | `/api/v1/certificates/{certificate_id}` | Api Get Certificate |
| POST | `/api/v1/check/audio` | Api Check Audio |
| POST | `/api/v1/check/impersonation` | Api Check Impersonation |
| POST | `/api/v1/check/media` | Api Check Media |
| POST | `/api/v1/check/text` | Api Check Text |
| GET | `/api/v1/checks/recent` | Api Recent Checks |
| GET | `/api/v1/checks/{check_id}` | Api Get Check |
| GET | `/api/v1/citizen/dashboard` | Api Citizen Dashboard |
| GET | `/api/v1/evidence` | Api List Evidence |
| POST | `/api/v1/evidence` | Api Register Evidence |
| GET | `/api/v1/evidence/` | Api List Evidence |
| POST | `/api/v1/evidence/` | Api Register Evidence |
| GET | `/api/v1/evidence/exports/{export_id}/verify` | Api Verify Export |
| GET | `/api/v1/evidence/health` | Api Vault Health |
| POST | `/api/v1/evidence/retention/run` | Api Retention |
| GET | `/api/v1/evidence/{evidence_id}` | Api Get Evidence |
| GET | `/api/v1/evidence/{evidence_id}/custody` | Api Custody |
| GET | `/api/v1/evidence/{evidence_id}/download` | Api Download Evidence |
| POST | `/api/v1/evidence/{evidence_id}/export` | Api Export |
| POST | `/api/v1/evidence/{evidence_id}/transfer` | Api Transfer |
| GET | `/api/v1/governance/compliance` | Api Compliance |
| GET | `/api/v1/governance/consent` | Api List Consent |
| POST | `/api/v1/governance/consent` | Api Upsert Consent |
| GET | `/api/v1/governance/controls` | Api Controls |
| GET | `/api/v1/governance/dataset-cards` | Api Dataset Cards |
| GET | `/api/v1/governance/features` | Api List Features |
| GET | `/api/v1/governance/health` | Api Governance Health |
| GET | `/api/v1/governance/model-cards` | Api Model Cards |
| GET | `/api/v1/governance/risks` | Api List Risks |
| PATCH | `/api/v1/governance/risks/{risk_id}` | Api Update Risk |
| GET | `/api/v1/incidents` | Api List Incidents |
| POST | `/api/v1/incidents` | Api Create Incident |
| GET | `/api/v1/incidents/{report_id}` | Api Get Incident |
| PATCH | `/api/v1/incidents/{report_id}` | Api Update Incident |
| GET | `/api/v1/incidents/{report_id}/timeline` | Api Incident Timeline |
| POST | `/api/v1/incidents/{report_id}/transition` | Api Transition Incident |
| POST | `/api/v1/infra/jobs/ai-evaluation` | Api Enqueue Ai Eval |
| POST | `/api/v1/infra/jobs/intel-ingest/{source_id}` | Api Enqueue Intel |
| POST | `/api/v1/infra/jobs/vault-retention` | Api Enqueue Retention |
| GET | `/api/v1/infra/status` | Api Infra Status |
| GET | `/api/v1/institution-portal/health` | Api Portal Health |
| GET | `/api/v1/institution-portal/{institution_id}/analytics` | Api Analytics |
| GET | `/api/v1/institution-portal/{institution_id}/api-keys` | Api List Keys |
| POST | `/api/v1/institution-portal/{institution_id}/api-keys` | Api Create Key |
| DELETE | `/api/v1/institution-portal/{institution_id}/api-keys/{key_id}` | Api Revoke Key |
| GET | `/api/v1/institution-portal/{institution_id}/branding` | Api Get Branding |
| PUT | `/api/v1/institution-portal/{institution_id}/branding` | Api Put Branding |
| GET | `/api/v1/institution-portal/{institution_id}/domains` | Api List Domains |
| POST | `/api/v1/institution-portal/{institution_id}/domains` | Api Add Domain |
| POST | `/api/v1/institution-portal/{institution_id}/domains/{domain_id}/verify` | Api Verify Domain |
| GET | `/api/v1/institution-portal/{institution_id}/investigations` | Api Investigations |
| GET | `/api/v1/institution-portal/{institution_id}/memberships` | Api List Memberships |
| POST | `/api/v1/institution-portal/{institution_id}/memberships` | Api Add Membership |
| PATCH | `/api/v1/institution-portal/{institution_id}/memberships/{membership_id}` | Api Update Membership |
| GET | `/api/v1/institution-portal/{institution_id}/official-accounts` | Api List Accounts |
| POST | `/api/v1/institution-portal/{institution_id}/official-accounts` | Api Add Account |
| DELETE | `/api/v1/institution-portal/{institution_id}/official-accounts/{account_id}` | Api Delete Account |
| GET | `/api/v1/institution-portal/{institution_id}/overview` | Api Overview |
| GET | `/api/v1/institutions` | Api List Institutions |
| POST | `/api/v1/institutions` | Api Create Institution |
| GET | `/api/v1/institutions-admin/overview` | Api Institutions Admin Overview |
| GET | `/api/v1/institutions/{institution_id}` | Api Get Institution |
| PATCH | `/api/v1/institutions/{institution_id}` | Api Update Institution |
| GET | `/api/v1/intel/campaigns` | Api Campaigns |
| POST | `/api/v1/intel/correlate` | Api Correlate |
| GET | `/api/v1/intel/correlations` | Api Correlations |
| GET | `/api/v1/intel/items` | Api List Items |
| GET | `/api/v1/intel/reports/national` | Api National Report |
| GET | `/api/v1/intel/source-classes` | Api Source Classes |
| GET | `/api/v1/intel/sources` | Api List Sources |
| POST | `/api/v1/intel/sources` | Api Create Source |
| PATCH | `/api/v1/intel/sources/{source_id}` | Api Patch Source |
| POST | `/api/v1/intel/sources/{source_id}/ingest` | Api Ingest Source |
| POST | `/api/v1/intel/webhook/{source_id}` | Api Webhook Ingest |
| POST | `/api/v1/intelligence/analyze` | Api Intelligence Analyze |
| POST | `/api/v1/intelligence/analyze/media` | Api Intelligence Analyze Media |
| GET | `/api/v1/intelligence/engines` | Api List Engines |
| GET | `/api/v1/notifications` | Api List Notifications |
| POST | `/api/v1/notifications/{notification_id}/read` | Api Mark Read |
| GET | `/api/v1/ntoc/dashboard` | Api Ntoc Dashboard |
| GET | `/api/v1/ntoc/institution-health` | Api Institution Health |
| GET | `/api/v1/ntoc/regions` | Api Ntoc Regions |
| GET | `/api/v1/ntoc/threat-level` | Api Threat Level |
| POST | `/api/v1/oauth/clients` | Register Oauth Client |
| POST | `/api/v1/oauth/token` | Oauth Token |
| GET | `/api/v1/partners/keys` | Api List Partner Keys |
| POST | `/api/v1/partners/keys` | Api Create Partner Key |
| DELETE | `/api/v1/partners/keys/{key_id}` | Api Revoke Partner Key |
| GET | `/api/v1/partners/me` | Api Partner Me |
| POST | `/api/v1/users` | Api Create User |
| GET | `/api/v1/users/{user_id}` | Api Get User |
| GET | `/api/v1/workflow/states` | Api Workflow States |
| GET | `/health` | Health |
| GET | `/metrics` | Metrics |
| GET | `/verify/a/{announcement_id}` | Public Verify Announcement |
| GET | `/verify/a/{announcement_id}/certificate` | Public Certificate |
