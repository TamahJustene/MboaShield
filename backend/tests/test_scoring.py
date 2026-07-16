from backend.app.services.text_check import check_text
from backend.app.services.impersonation import check_impersonation
from backend.app.services.audio_check import check_audio_bytes
from backend.app.services.source_verify import verify_claim
import wave
import struct
import io
import math


def test_high_risk_rumour():
    result = check_text(
        "URGENT: le ministre annonce un couvre-feu national. Envoie de l'argent au numero MoMo.",
        "fr",
    )
    assert result.risk_score >= 70
    assert result.risk_band == "high"


def test_impersonation_spoof():
    result = check_impersonation("MINPOSTEL Officiel Verifie", "@minpostel_cm_info", "en")
    assert result.is_suspicious is True
    assert result.risk_score >= 40


def test_source_verify_scam():
    v = verify_claim(
        "URGENT le ministre annonce couvre-feu. Envoyez argent MoMo maintenant.",
        "fr",
    )
    assert v.status == "likely_scam"
    assert len(v.scam_signals) >= 1


def _make_flat_wav() -> bytes:
  buf = io.BytesIO()
  rate = 16000
  duration = 2
  n = rate * duration
  with wave.open(buf, "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(rate)
    frames = b"".join(struct.pack("<h", int(3000 * math.sin(2 * math.pi * 440 * i / rate))) for i in range(n))
    wf.writeframes(frames)
  return buf.getvalue()


def test_audio_clone_signal():
    data = _make_flat_wav()
    result = check_audio_bytes(data, "minister_voice_urgent.wav", "en")
    assert result.risk_score >= 40
