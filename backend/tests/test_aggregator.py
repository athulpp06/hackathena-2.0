from backend.app.detector.aggregator import aggregate


def test_aggregate_safe():
    ml_score = 0.1
    rule_flags = []
    verifier_result = {"domain_mismatch": False, "suspicious_email": False}

    result = aggregate(ml_score, rule_flags, verifier_result)

    assert result["risk_score"] == 6  # 0.1 * 60
    assert result["risk_level"] == "Safe"
    assert "This job posting appears legitimate." in result["verdict"]

def test_aggregate_critical():
    ml_score = 0.95
    rule_flags = [{"category": "Financial Demand", "severity": "CRITICAL"}]
    verifier_result = {"domain_mismatch": True, "suspicious_email": True}

    result = aggregate(ml_score, rule_flags, verifier_result)

    # 0.95 * 60 = 57
    # CRITICAL rule = 20
    # Mismatch = 10
    # Total = 87
    assert result["risk_score"] == 87
    assert result["risk_level"] == "High Risk"
    assert "Critical Scam Indicators" in result["verdict"]

def test_aggregate_rule_cap():
    ml_score = 0.0
    rule_flags = [
        {"severity": "CRITICAL"},
        {"severity": "CRITICAL"},
        {"severity": "CRITICAL"}
    ]
    verifier_result = {"domain_mismatch": False, "suspicious_email": False}

    result = aggregate(ml_score, rule_flags, verifier_result)

    # Rules score: 3 * 20 = 60, capped at 40.
    # CRITICAL floor applies: at least one CRITICAL rule → score bumped to >= 51.
    # So score == 51, level == "Suspicious".
    assert result["risk_score"] == 51
    assert result["risk_level"] == "Suspicious"


def test_aggregate_critical_floor():
    """A single CRITICAL rule must always produce at least 51 (Suspicious), even with ML=0."""
    ml_score = 0.0
    rule_flags = [{"severity": "CRITICAL", "category": "Financial Demand"}]
    verifier_result = {"domain_mismatch": False, "suspicious_email": False}

    result = aggregate(ml_score, rule_flags, verifier_result)

    # CRITICAL rule = 20pts; ML=0; no domain penalty → raw=20, but floor kicks in → 51
    assert result["risk_score"] == 51
    assert result["risk_level"] == "Suspicious"


def test_aggregate_no_critical_no_floor():
    """Without any CRITICAL rules, a HIGH rule alone should NOT trigger the floor."""
    ml_score = 0.0
    rule_flags = [{"severity": "HIGH", "category": "Urgency / Pressure"}]
    verifier_result = {"domain_mismatch": False, "suspicious_email": False}

    result = aggregate(ml_score, rule_flags, verifier_result)

    # HIGH = 10 pts, no floor → stays at 10
    assert result["risk_score"] == 10
    assert result["risk_level"] == "Safe"
