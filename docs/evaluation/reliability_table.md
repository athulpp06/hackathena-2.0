# Calibration and Score Reliability Analysis

## ML Probability vs Final Aggregated Risk Score

LeakedIn uses a two-tier scoring architecture:
1. **Tier 1 (ML Layer):** TF-IDF features mapped to probabilities via `LogisticRegression` calibrated with `CalibratedClassifierCV(method='isotonic', cv=5)`.
2. **Tier 2 (Unified Threat Aggregator):** A domain-specific weighted risk score (0–100) combining isotonic ML likelihood (up to 60 points), heuristic rule severities (capped at 40 points), domain mismatch penalties (10 points), and community reputation boosts.

> **Honesty Disclosure:** The ML probability output is statistically calibrated via isotonic regression. However, the final 0–100 score is a **hand-weighted risk score**, not a Bayesian posterior probability. Documentation and client interfaces describe this metric as the **Weighted Scam Risk Score**.

---

## Empirical Reliability Table: ML Output (EMSCAD Test Split)

Measured across 10 probability bins on the 20% holdout test set (3,576 samples):

| Probability Range | Mean Predicted Fraud Probability | Actual Empirical Fraud Rate | Sample Count | Reliability Assessment |
|:---:|:---:|:---:|:---:|:---|
| `[0.00, 0.10)` | 0.006 | 0.004 | 3,365 | Highly calibrated safe baseline. |
| `[0.10, 0.20)` | 0.144 | 0.096 | 42 | Slight conservative over-prediction. |
| `[0.20, 0.30)` | 0.249 | 0.083 | 24 | Moderate conservative margin. |
| `[0.30, 0.40)` | 0.353 | 0.875 | 8 | Step transition in isotonic curve. |
| `[0.40, 0.50)` | 0.453 | 0.643 | 14 | Transition region. |
| `[0.50, 0.60)` | 0.562 | 0.500 | 6 | **Exact calibration** at 0.50 decision boundary. |
| `[0.60, 0.70)` | 0.648 | 1.000 | 7 | 100% precision in high-risk zone. |
| `[0.70, 0.80)` | 0.749 | 1.000 | 12 | 100% precision. |
| `[0.80, 0.90)` | 0.842 | 0.913 | 23 | High alignment with ground truth. |
| `[0.90, 1.00]` | 0.987 | 1.000 | 75 | 100% precision on high-confidence scams. |

---

## Reliability Table: Unified Aggregated Risk Score (Real-World Holdout)

Measured on the 125-sample out-of-sample real-world holdout dataset:

| Risk Score Interval | Assigned Risk Category | Actual Scam Proportion | Precision | Decision Action |
|:---:|:---:|:---:|:---:|:---|
| **0 – 25** | **Safe** | 4.8% (3/62) | 95.2% | Verified safe recruiter communication. |
| **26 – 50** | **Low Risk** | 22.2% (2/9) | 77.8% | Informational notice; verify company domain. |
| **51 – 75** | **Suspicious** | 88.9% (8/9) | 88.9% | Proceed with extreme caution. |
| **76 – 100** | **High Risk** | 97.8% (44/45) | **97.8%** | Critical scam indicators detected. Do not pay. |
