#!/usr/bin/env python3
"""Generate MboaShield SIN 2026 PowerPoint deck (Phase 15 / competition)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "presentations"
STATIC_OUT = ROOT / "frontend" / "static" / "presentations"
FILENAME = "MboaShield_SIN2026.pptx"

try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Install python-pptx: pip install python-pptx") from exc

SLIDES: list[tuple[str, list[str]]] = [
    (
        "MboaShield",
        [
            "Sovereign AI shield against deepfakes, disinformation and digital identity theft",
            "Made in Cameroon - SIN 2026 National Best ICT Project",
            "Solo founder: Justene Nkwagoh Tamah",
            "Theme: Protect cyberspace from AI excesses and digital patriotism",
        ],
    ),
    (
        "The problem (Cameroon, today)",
        [
            "Fake minister announcements and curfew hoaxes on WhatsApp",
            "Voice clones demanding MoMo transfers",
            "Deepfake images targeting institutions and public figures",
            "Youth forward before verifying - fraud, panic, eroded trust",
        ],
    ),
    (
        "The solution",
        [
            "Detect synthetic media and scam patterns",
            "Verify rumours and flag fake official accounts",
            "Train Mboa Ambassadors in digital patriotism",
            "WhatsApp-first narrative - FR/EN - privacy by design - sovereign stack",
        ],
    ),
    (
        "Live demo (90 seconds)",
        [
            "1. Viral rumour - risk score and source check",
            "2. Fake MINPOSTEL-style account - impersonation",
            "3. Minister voice sample - clone risk",
            "4. Suspicious image - synthetic signals",
            "5. Mboa Ambassador certificate",
            "Demo: mboashield.onrender.com - Run Grand Jury demo",
        ],
    ),
    (
        "Platform depth (v1.9.0)",
        [
            "National incident workflow with human gates (no auto-public advisory)",
            "NTOC, intel, investigation, evidence vault, signed government announcements",
            "AI platform: model registry, golden EN/FR evaluation, certainty: none",
            "Governance: consent, risk register, model and dataset cards",
        ],
    ),
    (
        "Innovation and AI (honest)",
        [
            "Text, audio, image, identity, civic modules - multimodal trust engine",
            "17-institution registry for local impersonation detection",
            "Heuristic and registry today; ONNX path with checksums for production",
            "Differentiator: Cameroon WhatsApp context, institutions, civic mission",
        ],
    ),
    (
        "Impact and digital patriotism",
        [
            "Citizens: free checks and education",
            "Schools and youth: Mboa Ambassadors",
            "Media, banks, telcos: B2B API",
            "Government: registry, verified comms, national analytics",
        ],
    ),
    (
        "Business model",
        [
            "Citizen Check: free (mission and sponsors)",
            "Pro: media/SMEs - 75k to 250k FCFA/month",
            "Enterprise: banks/telcos - annual API",
            "Ambassadors: schools - training packs",
            "Year 1 target: pilots and 18-25M FCFA revenue path",
        ],
    ),
    (
        "The ask",
        [
            "Special Prize of the President of the Republic to:",
            "1. Industrialise MboaShield nationally",
            "2. Launch institutional identity registry v1 at scale",
            "3. Train 50,000 Mboa Ambassadors in Year 1",
            "MboaShield IS the 2026 theme - not adjacent to it.",
            "tamahjustene45@gmail.com - github.com/TamahJustene/MboaShield",
        ],
    ),
]


def _add_bullet_slide(prs: Presentation, title: str, bullets: list[str]) -> None:
    layout = prs.slide_layouts[1]
    slide = prs.slides.add_slide(layout)
    slide.shapes.title.text = title
    body = slide.placeholders[1].text_frame
    body.clear()
    first = True
    for line in bullets:
        if not line.strip():
            continue
        if first:
            p = body.paragraphs[0]
            first = False
        else:
            p = body.add_paragraph()
        p.text = line
        p.level = 0
        p.font.size = Pt(20)


def build() -> Path:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    title_slide = prs.slides.add_slide(prs.slide_layouts[0])
    title_slide.shapes.title.text = SLIDES[0][0]
    title_slide.placeholders[1].text = "\n".join(SLIDES[0][1])

    for title, bullets in SLIDES[1:]:
        _add_bullet_slide(prs, title, bullets)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    STATIC_OUT.mkdir(parents=True, exist_ok=True)
    path_docs = OUT_DIR / FILENAME
    path_static = STATIC_OUT / FILENAME
    prs.save(path_docs)
    prs.save(path_static)
    return path_docs


def main() -> int:
    path = build()
    print(f"Wrote {path}")
    print(f"Wrote {STATIC_OUT / FILENAME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
