from backend.app.services.text_check import check_text
from backend.app.services.impersonation import check_impersonation


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
