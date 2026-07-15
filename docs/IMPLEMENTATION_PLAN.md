# Implementation Plan  MboaShield MVP (solo)

Owner: **Justene Nkwagoh Tamah**  
Goal: rock-solid **90-second live demo** for pitch **30 July 2026**  
Today: **15 July 2026** ? ~15 days to pitch; dossier due **22 July 15:30**

---

## Phase 0  Competition paperwork (TODAY ? 21 July)
| Task | Done when |
|---|---|
| Personalise & submit `MboaShield.pdf` + form | Confirmation on ictinnovationweek.cm before 22 Jul 15:30 |
| Record 30s elevator video (optional but useful) | Link ready |
| List WhatsApp number for form | Form complete |

## Phase 1  Demo spine (1518 July) ? YOU ARE HERE
| Day | Build | Acceptance |
|---|---|---|
| D0 | Repo + FastAPI + static UI shell | `/health` 200 + homepage loads |
| D1 | Text claim checker + institutions/sources data | False viral claim scores HIGH with explanation |
| D1 | Impersonation checker | MINPOSTEL Officiel Fake flagged |
| D2 | Image heuristic check + sample images | Upload returns risk band + reasons |
| D2 | Ambassadors lessons + certificate stub | Name ? certificate card on screen |

## Phase 2  Pitch hardness (1922 July)
| Task | Acceptance |
|---|---|
| Scripted 90s demo path hardcoded as Demo Mode | One-click runs 3 scenarios |
| FR/EN toggle on UI | Jury can follow in either language |
| Backup: screen-record demo MP4 on USB | Works if Wi-Fi dies |
| Unit tests for scorers | `pytest` green |

## Phase 3  Polish & narrative (2326 July)
| Task | Acceptance |
|---|---|
| Landing copy matches dossier story | Theme words visible |
| Architecture one-pager PDF for jury if asked | 1 page |
| Rehearse pitch from `PITCH_3_MINUTES.md` × 10 | Timed ? 3:00 |

## Phase 4  Bootcamp & final (2730 July)
| Task | Acceptance |
|---|---|
| Absorb mentors; cut anything flaky | Only stable features on stage |
| Marketing video 6090s | Required by Grand Jury rules |
| Final pitch deck 810 slides | Problem ? Demo ? Business ? Ask |

---

## Out of scope before pitch (do later)
- Full deepfake neural net training from scratch
- Production WhatsApp Business billing
- Multi-tenant SaaS billing
- National institutional contracts

## Success metric
Jury can *see* MboaShield work: suspicion ? risk score ? explanation ? civic certificate, in under 90 seconds, offline if needed.
