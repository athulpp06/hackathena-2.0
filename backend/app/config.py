"""
config.py - Configuration settings for the LeakedIn backend.
"""

# ---------------------------------------------------------------------------
# Aggregator Weights
# ---------------------------------------------------------------------------
# Maximum points the ML model can contribute to the final risk score.
AGGREGATOR_ML_WEIGHT = 60.0

# Maximum points the Rule Engine can contribute to the final risk score.
AGGREGATOR_RULE_MAX_CAP = 40.0

# Points assigned per rule severity
AGGREGATOR_RULE_SEVERITY_POINTS = {
    "CRITICAL": 20.0,
    "HIGH": 10.0,
    "MEDIUM": 5.0,
    "LOW": 2.0
}

# Penalty points for domain mismatches or suspicious emails
AGGREGATOR_DOMAIN_MISMATCH_PENALTY = 10.0
