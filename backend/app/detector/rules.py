"""
Rule-Based Scam Detection Engine (Multilingual & Normalization-Aware).
Extracts high-precision fraud patterns, categorizes threat vectors, and computes exact character spans.
"""

import os
import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

import yaml

from backend.app.utils.normalizer import normalize_with_mapping

PATTERNS_FILE = os.path.join(os.path.dirname(__file__), "patterns", "rules.yaml")


@dataclass
class RedFlag:
    category: str
    severity: str         # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    penalty: int          # Score penalty (0-100 scale impact)
    title: str
    explanation: str
    matched_text: str
    start: int
    end: int

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["message"] = self.explanation  # Compatibility with v2
        return d


# Rule definitions: (category, severity, penalty, title, explanation, regex_patterns)
SCAM_RULES = [
    # ----------------------------------------------------
    # 1. UPFRONT FINANCIAL DEMANDS (CRITICAL)
    # ----------------------------------------------------
    (
        "Financial Demand",
        "CRITICAL",
        50,
        "Upfront Fee / Registration Charge",
        "Legitimate employers never demand application fees, registration charges, or initial payments to apply or start working.",
        [
            r"(?:registration|processing|application|portal|verification|screening|training|joining)\s*(?:fee|charges?|deposit|amount|cost)\s*(?:of|is|:)?\s*(?:₹|rs\.?|inr|\$|usd|eur|€)?\s*\d+",
            r"(?:pay|deposit|transfer|send)\s*(?:₹|rs\.?|inr|\$|usd|eur|€)?\s*\d+\s*(?:before|for|as|towards)?\s*(?:joining|interview|kit|training|laptop|offer)",
            r"(?:refundable|security)\s*(?:deposit|fee|amount)\s*(?:of|is|:)?\s*(?:₹|rs\.?|inr|\$|usd|eur|€)?\s*\d*",
            r"\b(?:just\s+|only\s+)?(?:pay|deposit|transfer|invest)\s*(?:₹|rs\.?|inr|\$|usd|eur|€)?\s*\d+\s*(?:initially|upfront|in\s*advance|first|to\s*start|to\s*join)\b",
            r"\b(?:initial\s+payment|initial\s+deposit|initial\s+charge|pay\s+initially|pay\s+upfront)\s*(?:of|is|:)?\s*(?:₹|rs\.?|inr|\$|usd|eur|€)?\s*\d*",
            r"\bjust\s+pay\s+(?:₹|rs\.?|inr|\$)?\s*\d+\b",
            r"\b(?:pay to apply|fee required|deposit required|upfront payment|nominal fee|one-time charge)\b",
        ]
    ),
    (
        "Financial Demand",
        "CRITICAL",
        40,
        "Mandatory Equipment or Software Purchase",
        "Scammers often claim you must buy specific software, hardware, or home office kits from their 'approved vendor'.",
        [
            r"(?:buy|purchase)\s+(?:your\s+own\s+)?(?:laptop|equipment|software|kit|tools)\s+(?:from\s+our\s+vendor|upfront)",
            r"(?:training|orientation|starter)\s+(?:kit|materials?|software)\s+(?:fee|charges?|cost)",
            r"(?:pay\s+for|purchase\s+a)\s+background\s+check",
        ]
    ),
    (
        "Financial Demand",
        "CRITICAL",
        50,
        "Cheque or Crypto Payment Scheme",
        "Fake cheque and crypto schemes involve sending fraudulent checks for home office equipment or demanding crypto transfers.",
        [
            r"\b(?:cash\s+our\s+che?ck|deposit\s+(?:the\s+)?che?ck|wire\s+the\s+remainder|send\s+back\s+excess)\b",
            r"\b(?:equipment\s+che?ck|home\s+office\s+(?:equipment\s+)?che?ck|che?ck\s+for\s+(?:home\s+office|supplies|equipment|setup))\b",
            r"\b(?:western\s+union|moneygram|bitcoin|crypto|usdt|binance|gift\s*card)\b",
        ]
    ),

    # ----------------------------------------------------
    # 2. SUSPICIOUS COMMUNICATION CHANNELS (HIGH)
    # ----------------------------------------------------
    (
        "Suspicious Contact",
        "HIGH",
        30,
        "Telegram / WhatsApp-Only Recruiter",
        "Professional hiring managers communicate via enterprise emails or portals, not private Telegram or WhatsApp chats.",
        [
            r"(?:contact|message|dm|reach|chat\s+with|interview\s+on|proceed\s+on)\s+(?:our\s+)?(?:hiring\s+)?(?:hr|recruiter|manager)?\s*(?:immediately|asap|now)?\s*(?:via|on|through|at)?\s*[:\-]?\s*(?:telegram|whatsapp)\b",
            r"\b(?:telegram|whatsapp)\s*(?:handle|id|contact|desk|username|channel)?\s*[:\-]?\s*@[a-zA-Z0-9_]{3,}\b",
            r"(?:t\.me\/[a-zA-Z0-9_]+|wa\.me\/[0-9]+)",
            r"(?:send\s+(?:cv|resume|details)\s+(?:on|to|via)\s+(?:whatsapp|telegram))\b",
            r"\bwhatsapp\s*(?:no|number|contact)?\s*[:\-]?\s*(?:\+?\d[\d\s\-]{8,15}\d)",
        ]
    ),
    (
        "Suspicious Contact",
        "HIGH",
        25,
        "Generic Free Webmail for Corporate Hiring",
        "Free webmail addresses (Gmail, Yahoo, Hotmail) used for established corporate or MNC hiring is a primary indicator of impersonation.",
        [
            r"[a-zA-Z0-9_.+-]+@(?:gmail|yahoo|hotmail|outlook|rediffmail|protonmail|aol)\.com\b",
        ]
    ),

    # ----------------------------------------------------
    # 3. STUDENT & INTERNSHIP EXPLOITATION (HIGH)
    # ----------------------------------------------------
    (
        "Too Good To Be True",
        "HIGH",
        35,
        "Student Internship / Pocket Money Bait",
        "Scammers target college students with promises of easy pocket money or fast hiring while demanding upfront money.",
        [
            r"\b(?:earn|make)\s+(?:more\s+than\s+)?(?:your\s+)?pocket\s*money\b",
            r"\b(?:pursuing\s+students|college\s+students|school\s+students)\b[^\n.!?]{0,100}\b(?:earn|pocket\s*money)\b",
            r"\bfor\s+pursuing\s+students\s*(?:\([^)]*\))?\s*where\s+you\s+can\s+earn\b",
            r"\b(?:part-time|remote)\s+job\s+for\s+(?:pursuing|college)\s+students\b",
        ]
    ),
    (
        "Contradictory Claims",
        "HIGH",
        35,
        "Paid Fee for 'Free' Internship Claim",
        "Claiming to be a 'Free internship' while simultaneously demanding an upfront fee or initial payment is a deceptive fraud tactic.",
        [
            r"\bfree\s+internship\b[\s\S]{0,500}\b(?:pay|fee|deposit|charges?)\b",
            r"\b(?:pay|fee|deposit|charges?)\b[\s\S]{0,500}\bfree\s+internship\b",
        ]
    ),
    (
        "Suspicious Contact",
        "HIGH",
        30,
        "Informal Questionnaire Application Template",
        "Broadcasting fill-in-the-blank text questionnaires (Name, College, Branch, Phone) instead of official career portals is typical of unregulated scam broadcasts.",
        [
            r"(?:TO\s*APPLY\s*(?:FILL|SEND)?[:\s]*)?NAME:\s*\n?\s*(?:COLLEGE|BRANCH|DEGREE)[:\s]+[\s\S]*?(?:STATE\s*(?:YOU\s*BELONG\s*TO)?|CITY|LANGUAGE|EMAIL[:\s]*|PH(?:ONE)?[:\s]*)",
            r"TO\s*APPLY\s*(?:FILL|SEND)?[:\s]+NAME:[\s\S]*?(?:COLLEGE|BRANCH|PHONE|PH:)",
            r"\bFILL\s+(?:THE\s+)?BELOW\s+DETAILS[:\s]+NAME:[\s\S]*?(?:COLLEGE|BRANCH|PHONE|PH:)",
        ]
    ),

    # ----------------------------------------------------
    # 4. UNREALISTIC OFFERS & COMPENSATION (HIGH)
    # ----------------------------------------------------
    (
        "Too Good To Be True",
        "HIGH",
        30,
        "Exorbitant Pay for Low-Skill Work",
        "Unusually high compensation promised for simple tasks like data entry, copy-paste, or typing is a classic bait-and-switch scam.",
        [
            r"(?:good\s+)?stipend\s*(?::|is)?\s*\(?(?:₹|rs\.?|inr|\$)?\s*\d+\s*(?:-|to)\s*(?:₹|rs\.?|inr|\$)?\s*\d+\)?",
            r"(?:data\s*entry|copy\s*paste|form\s*filling|typing|sms\s*sending)\s*(?:job|work)?\s*(?:earn|pays?|salary)?\s*(?:₹|rs\.?|inr|\$)?\s*(?:[3-9]\d|\d{3,})\s*(?:k|thousand|\/|\s*per\s*)(?:day|week|month)",
            r"(?:earn|salary|make)\s*(?:₹|rs\.?|inr|\$)\s*[4-9]\d{3,}\s*(?:per\s*week|\/week|daily|per\s*day)",
            r"(?:compensation|salary|pay|earn|rate)\s*[:\-]?\s*\$\s*[3-9]\d\s*\/?\s*(?:hr|hour)",
            r"(?:no\s+(?:prior\s+)?experience\s+(?:required|needed))\b",
            r"\b(?:earn\s+while\s+you\s+sleep|guaranteed\s+daily\s+income|100%\s+guaranteed\s+job)\b",
        ]
    ),

    # ----------------------------------------------------
    # 5. FAKE URGENCY & PRESSURE TACTICS (HIGH / MEDIUM)
    # ----------------------------------------------------
    (
        "Urgency / Pressure",
        "HIGH",
        25,
        "No Interview or Instant Selection",
        "Genuine corporate roles require formal evaluations. Offers made without an interview or screening are universally fraudulent.",
        [
            r"\b(?:direct\s+selection|no\s+interview\s+(?:needed|required)|immediate\s+selection|instant\s+offer\s+letter|spot\s+offer)\b",
            r"\b(?:selected\s+without\s+interview|hired\s+immediately\s+without\s+test)\b",
            r"\b(?:immediate\s+hiring|urgently\s+hiring|spot\s+joining|urgent\s+hiring)\b",
        ]
    ),
    (
        "Urgency / Pressure",
        "MEDIUM",
        15,
        "Artificial Urgency / Pressure Tactics",
        "Creating false urgency ('join within 24h', 'limited slots') is designed to panic victims into paying before verifying legitimacy.",
        [
            r"\b(?:offer\s+(?:valid|expires)\s+(?:for|within)?\s*\d+\s*(?:hours|hrs|mins)|urgent\s+joining\s+today|only\s+\d+\s+seats?\s+left)\b",
            r"\b(?:act\s+fast|first\s+come\s+first\s+served|hurry\s+up|closing\s+in\s+few\s+hours)\b",
        ]
    ),

    # ----------------------------------------------------
    # 6. SENSITIVE PERSONAL DATA HARVESTING & OTP THEFT (CRITICAL)
    # ----------------------------------------------------
    (
        "Identity Theft",
        "CRITICAL",
        45,
        "Premature Sensitive Identity Request (Aadhaar / PAN / Bank)",
        "Asking for national IDs (Aadhaar, PAN, SSN) or banking credentials before a formal interview or contract is an identity theft risk.",
        [
            r"\b(?:send|submit|share)\s+(?:your\s+)?(?:aadhaar|pan\s+card|social\s+security|ssn|bank\s+account\s+details|debit\s+card)\b",
            r"(?:send|upload|submit|share|provide|attach|forward|email|whatsapp)\s.{0,25}(?:aadhaar|aadhar|adhar|pan\s*card|pan\s*number|passport\s*copy|bank\s*(?:account|details|statement)|account\s*number|ifsc)",
            r"(?:ആധാർ\s*(?:കൊണ്ടുവരൂ|അയക്കൂ|ഷെയർ|നൽകൂ|കോപ്പി)|ബാങ്ക്\s*(?:അക്കൗണ്ട്|ഡീറ്റെയിൽസ്)\s*(?:അയക്കൂ|നൽകൂ|ഷെയർ)|പാൻ\s*(?:കാർഡ്\s*)?(?:അയക്കൂ|ഷെയർ|നൽകൂ)|ഐഡി\s*(?:പ്രൂഫ്\s*)?(?:അയക്കൂ|നൽകൂ))",
            r"(?:आधार\s*(?:कार्ड\s*)?(?:भेजें|शेयर|दें|अपलोड)|पैन\s*(?:कार्ड\s*)?(?:भेजें|शेयर|दें)|बैंक\s*(?:विवरण|डिटेल)\s*(?:भेजें|दें|शेयर))",
            r"(?:aadhaar\s*(?:bhejo|send|share|de|upload|submit)|pan\s*(?:bhejo|card\s*de|share|upload)|bank\s*details\s*(?:bhejo|share|de|send)|aadhar\s*card\s*(?:ka\s*photo|copy)\s*(?:bhejo|send|do|upload))",
            r"\b(?:upload|provide)\s+(?:scanned\s+copy\s+of\s+)?(?:passport|voter\s+id)\s+(?:for\s+shortlisting|to\s+apply)\b",
        ]
    ),
    (
        "Identity Theft",
        "CRITICAL",
        50,
        "OTP Theft / Credential Hijacking",
        "Recruiters never request one-time passwords (OTP). Any request to share OTP indicates an active financial hijacking attempt.",
        [
            r"(?:share|send|give|bata|batao|bhejo|പറഞ്ഞ|ഷെയർ)\s.{0,20}\botp\b",
            r"\botp\s*(?:code|verification)?\s*[:\-]?\s*\d{4,6}\b",
            r"\botp\s.{0,20}(?:share|send|verify|confirm|enter)\b",
        ]
    ),
    (
        "Financial Demand",
        "CRITICAL",
        50,
        "Multilingual Fee Demand (Malayalam / Hindi / Hinglish)",
        "Demanding upfront registration charges in native regional languages (Malayalam, Hindi, Hinglish) is an urgent scam indicator.",
        [
            r"(?:രജിസ്ട്രേഷൻ\s*ഫീസ്|ഫീസ്\s*അടക്കണം|അഡ്വാൻസ്\s*(?:അടക്കണം|തരണം|നൽകണം)|ഡിപ്പോസിറ്റ്\s*(?:അടക്കണം|ആദ്യം)|പണം\s*(?:അയക്കണം|തരണം|ട്രാൻസ്ഫർ)|ആദ്യം\s*(?:അടക്കണം|പണം)|ഫീ\s*(?:അടക്കണം|ഉണ്ട്))",
            r"(?:रजिस्ट्रेशन\s*फीस|एडवांस\s*(?:दे|जमा)|फीस\s*(?:दें|जमा\s*करें|भेजें)|पैसे\s*(?:भेजो|ट्रांसफर|दो)|डिपॉजिट\s*(?:जमा|दें)|पंजीकरण\s*शुल्क)",
            r"(?:paise\s*(?:de|bhejo|do|transfer|bhej)|paisa\s*(?:lagega|chahiye|dena|jama)|fees?\s*(?:deni|pay|bharna|submit)|registration\s*(?:ka\s*)?paisa|advance\s*dena\s*(?:hoga|padega|hai))",
            r"(?:pay|send|transfer)\s.{0,30}@(?:okicici|oksbi|okaxis|okhdfc|ybl|upi|paytm|gpay|phonepe)\b",
        ]
    ),
]


class RuleEngine:
    """
    Scans job posting text against high-fidelity fraud rules.
    Outputs structured red flags with exact character coordinates.
    """

    def __init__(self):
        self.compiled_rules = []

        # 1. Compile SCAM_RULES
        for category, severity, penalty, title, explanation, patterns in SCAM_RULES:
            compiled_patterns = [re.compile(p, re.IGNORECASE) for p in patterns]
            self.compiled_rules.append({
                "category": category,
                "severity": severity,
                "penalty": penalty,
                "title": title,
                "explanation": explanation,
                "patterns": compiled_patterns,
            })

        # 2. Compile patterns from patterns/rules.yaml if present
        if os.path.exists(PATTERNS_FILE):
            try:
                with open(PATTERNS_FILE, encoding="utf-8") as f:
                    yaml_rules = yaml.safe_load(f) or []
                for yr in yaml_rules:
                    cat = yr.get("category", "General")
                    sev = yr.get("severity", "MEDIUM")
                    pen = {"CRITICAL": 45, "HIGH": 25, "MEDIUM": 15, "LOW": 5}.get(sev, 15)
                    title = yr.get("title") or yr.get("description") or f"{cat} Rule"
                    exp = yr.get("description", title)
                    regex_str = yr.get("regex", "")
                    if regex_str:
                        compiled = re.compile(regex_str, re.IGNORECASE | re.DOTALL)
                        self.compiled_rules.append({
                            "category": cat,
                            "severity": sev,
                            "penalty": pen,
                            "title": title,
                            "explanation": exp,
                            "patterns": [compiled],
                        })
            except Exception as e:
                print(f"Warning: Failed to load extra rules from {PATTERNS_FILE}: {e}")

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Executes all heuristic checks on input text with normalization offset mapping.
        """
        if not text or not text.strip():
            return {
                "red_flags": [],
                "flag_count": 0,
                "total_penalty": 0,
                "highlighted_spans": [],
                "summary": "No text provided for analysis."
            }

        norm_text, offset_map = normalize_with_mapping(text)

        detected_flags: List[RedFlag] = []
        matched_ranges = []

        for rule in self.compiled_rules:
            for pattern in rule["patterns"]:
                # Match against normalized text
                for match in pattern.finditer(norm_text):
                    norm_start = match.start()
                    norm_end = match.end() - 1

                    if norm_start > norm_end:
                        continue

                    # Map back to original indices
                    orig_start = offset_map[norm_start] if norm_start < len(offset_map) else match.start()
                    orig_end = (offset_map[norm_end] + 1) if norm_end < len(offset_map) else match.end()
                    matched_text = text[orig_start:orig_end]

                    if len(matched_text.strip()) < 2:
                        continue

                    # De-duplicate flags with same title in close proximity
                    is_duplicate = False
                    for existing in detected_flags:
                        if existing.title == rule["title"] and abs(existing.start - orig_start) < 20:
                            is_duplicate = True
                            break

                    if not is_duplicate:
                        flag = RedFlag(
                            category=rule["category"],
                            severity=rule["severity"],
                            penalty=rule["penalty"],
                            title=rule["title"],
                            explanation=rule["explanation"],
                            matched_text=matched_text,
                            start=orig_start,
                            end=orig_end,
                        )
                        detected_flags.append(flag)
                        matched_ranges.append((orig_start, orig_end, rule["severity"]))

        if not detected_flags:
            total_penalty = 0
        else:
            base_penalty = max(f.penalty for f in detected_flags)
            extra_penalty = sum(f.penalty for f in detected_flags) - base_penalty
            total_penalty = min(100, int(base_penalty + (extra_penalty * 0.4)))

        highlighted_spans = self._merge_spans(matched_ranges)

        return {
            "red_flags": [f.to_dict() for f in detected_flags],
            "flag_count": len(detected_flags),
            "total_penalty": total_penalty,
            "highlighted_spans": highlighted_spans,
        }

    def evaluate(self, text: str) -> List[Dict[str, Any]]:
        """Alias returning just the list of red flags."""
        return self.analyze(text)["red_flags"]

    def _merge_spans(self, spans: List[tuple]) -> List[Dict[str, Any]]:
        if not spans:
            return []

        sorted_spans = sorted(spans, key=lambda x: (x[0], x[1]))
        merged = []
        severity_rank = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}

        curr_start, curr_end, curr_sev = sorted_spans[0]

        for start, end, sev in sorted_spans[1:]:
            if start <= curr_end:
                curr_end = max(curr_end, end)
                if severity_rank.get(sev, 1) > severity_rank.get(curr_sev, 1):
                    curr_sev = sev
            else:
                merged.append({"start": curr_start, "end": curr_end, "severity": curr_sev})
                curr_start, curr_end, curr_sev = start, end, sev

        merged.append({"start": curr_start, "end": curr_end, "severity": curr_sev})
        return merged


_RULE_ENGINE = RuleEngine()


def detect_rules(text: str) -> List[Dict[str, Any]]:
    """Convenience function matching the v2 pipeline signature."""
    return _RULE_ENGINE.analyze(text)["red_flags"]
