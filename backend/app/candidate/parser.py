"""
Candidate Profile & Resume Ingestion and Structured Entity Parser (Module 1).
Supports PDF extraction, native OCR for image-based CVs, and plain text parsing.
Extracts contact information, educational timeline, work experience history,
skills, certifications, and declared references.
"""

import io
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

import pypdf
import asyncio
from backend.app.ocr import extract_text_from_image_bytes, is_ocr_available

# ── Contact Parsing Patterns ────────────────────────────────────────────────

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_REGEX = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3,5}\)?[-.\s]?\d{3,5}[-.\s]?\d{3,5}"
)
LINKEDIN_REGEX = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/([a-zA-Z0-9_-]+)", re.IGNORECASE)
GITHUB_REGEX = re.compile(r"(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9_-]+)", re.IGNORECASE)
PORTFOLIO_REGEX = re.compile(
    r"(?:https?://)?(?:www\.)?(?:[a-zA-Z0-9-]+\.)+(?:io|dev|me|site|tech|com|org)(?:/[^\s]*)?",
    re.IGNORECASE,
)

# ── Education Parsing Patterns ───────────────────────────────────────────────

DEGREE_PATTERNS = [
    (r"\b(?:ph\.?d|doctor\s+of\s+philosophy|doctorate)\b", "Doctorate / Ph.D"),
    (r"\b(?:m\.?tech|master\s+of\s+technology)\b", "M.Tech"),
    (r"\b(?:m\.?s(?:\.|\b)|master\s+of\s+science)\b", "M.S."),
    (r"\b(?:m\.?b\.?a|master\s+of\s+business\s+administration)\b", "MBA"),
    (r"\b(?:m\.?c\.?a|master\s+of\s+computer\s+applications)\b", "MCA"),
    (r"\b(?:b\.?tech|bachelor\s+of\s+technology)\b", "B.Tech"),
    (r"\b(?:b\.?e(?:\.|\b)|bachelor\s+of\s+engineering)\b", "B.E."),
    (r"\b(?:b\.?s\.?c|bachelor\s+of\s+science)\b", "B.Sc"),
    (r"\b(?:b\.?c\.?a|bachelor\s+of\s+computer\s+applications)\b", "BCA"),
    (r"\b(?:b\.?b\.?a|bachelor\s+of\s+business\s+administration)\b", "BBA"),
    (r"\b(?:b\.?com|bachelor\s+of\s+commerce)\b", "B.Com"),
    (r"\b(?:b\.?a(?:\.|\b)|bachelor\s+of\s+arts)\b", "B.A."),
    (r"\b(?:high\s+school|12th\s+grade|senior\s+secondary|hsc|cbse\s+xii)\b", "High School / 12th"),
    (r"\b(?:10th\s+grade|matriculation|ssc|cbse\s+x)\b", "Secondary / 10th"),
]

# Year range pattern, e.g. 2016 - 2020, 2019-2023, 2020 to 2024
EDU_YEAR_RANGE_REGEX = re.compile(
    r"\b(19\d{2}|20\d{2})\s*(?:-|–|—|to)\s*(19\d{2}|20\d{2}|present|expected|current)\b",
    re.IGNORECASE,
)
SINGLE_YEAR_REGEX = re.compile(r"\b(19\d{2}|20\d{2})\b")

CGPA_REGEX = re.compile(
    r"\b(?:cgpa|gpa|marks|percentage|aggregate)\s*[:=-]?\s*([0-9]{1,2}(?:\.[0-9]{1,2})?)\s*(?:/\s*(?:10|4)|%)?",
    re.IGNORECASE,
)

# ── Work Experience & Title Patterns ─────────────────────────────────────────

MONTH_MAP = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

MONTH_REGEX_STR = r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"

DATE_RANGE_REGEX = re.compile(
    rf"\b({MONTH_REGEX_STR}\.?\s+)?(19\d{{2}}|20\d{{2}})\s*(?:-|–|—|to)\s*({MONTH_REGEX_STR}\.?\s+)?(19\d{{2}}|20\d{{2}}|present|current|till\s+date|now)\b",
    re.IGNORECASE,
)

COMMON_JOB_TITLES = [
    "chief technology officer", "chief executive officer", "cto", "ceo", "vp of engineering",
    "vice president", "engineering manager", "director of engineering", "technical lead", "tech lead",
    "senior software engineer", "lead software engineer", "principal engineer", "staff software engineer",
    "senior systems engineer", "systems engineer", "software engineer", "backend engineer",
    "frontend engineer", "full stack engineer", "full stack developer", "python developer",
    "java developer", "devops engineer", "cloud architect", "solutions architect", "cloud engineer",
    "data scientist", "machine learning engineer", "ml engineer", "ai engineer", "data analyst",
    "systems analyst", "qa engineer", "product manager", "associate product manager", "software developer",
    "intern", "summer intern", "marketing intern", "research intern", "engineering intern",
    "graduate trainee", "management trainee", "trainee", "associate", "consultant",
]

# ── Tech Stack / Skills Inventory ───────────────────────────────────────────

COMMON_SKILLS = {
    "python", "javascript", "typescript", "java", "c++", "c#", "golang", "go", "rust",
    "ruby", "php", "swift", "kotlin", "sql", "nosql", "html", "css", "react", "react native",
    "angular", "vue", "vue.js", "next.js", "node.js", "express", "django", "flask", "fastapi",
    "spring", "spring boot", "docker", "kubernetes", "aws", "azure", "gcp", "google cloud",
    "git", "ci/cd", "graphql", "rest api", "kafka", "redis", "mongodb", "postgresql", "mysql",
    "sqlite", "dynamodb", "terraform", "ansible", "jenkins", "linux", "pandas", "numpy",
    "scikit-learn", "tensorflow", "pytorch", "opencv", "solidity", "web3", "flutter", "spark",
    "hadoop", "microservices", "agile", "scrum",
}


# ── Text Extraction Handlers ────────────────────────────────────────────────

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extracts plain text from PDF bytes using pypdf.
    """
    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        extracted_pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                extracted_pages.append(text.strip())
        return "\n\n".join(extracted_pages)
    except Exception as e:
        return f"[PDF_EXTRACTION_ERROR: {str(e)}]"


def extract_text_from_image(image_bytes: bytes) -> str:
    """
    Extracts text from image bytes using LeakedIn native OCR engine.
    """
    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                text, _ = pool.submit(asyncio.run, extract_text_from_image_bytes(image_bytes)).result()
        else:
            text, _ = asyncio.run(extract_text_from_image_bytes(image_bytes))
        return text
    except Exception as e:
        return f"[IMAGE_OCR_ERROR: {e}]"


# ── Entity Extractors ────────────────────────────────────────────────────────

def extract_contact_info(text: str) -> Dict[str, Any]:
    """
    Extracts candidate contact details and professional social profile URLs.
    """
    emails = list(set(EMAIL_REGEX.findall(text)))
    
    # Phone numbers
    phone_candidates = PHONE_REGEX.findall(text)
    clean_phones = []
    for p in phone_candidates:
        p_clean = re.sub(r"[^\d+]", "", p)
        if len(p_clean) >= 10 and len(p_clean) <= 15:
            clean_phones.append(p.strip())
    clean_phones = list(set(clean_phones))

    # LinkedIn
    linkedin_match = LINKEDIN_REGEX.search(text)
    linkedin_handle = linkedin_match.group(1) if linkedin_match else None
    linkedin_url = f"https://linkedin.com/in/{linkedin_handle}" if linkedin_handle else None

    # GitHub
    github_match = GITHUB_REGEX.search(text)
    github_handle = github_match.group(1) if github_match else None
    github_url = f"https://github.com/{github_handle}" if github_handle else None

    return {
        "emails": emails,
        "primary_email": emails[0] if emails else None,
        "phones": clean_phones,
        "primary_phone": clean_phones[0] if clean_phones else None,
        "linkedin_url": linkedin_url,
        "linkedin_handle": linkedin_handle,
        "github_url": github_url,
        "github_handle": github_handle,
    }


def extract_education(text: str) -> List[Dict[str, Any]]:
    """
    Extracts candidate degrees, institutions, graduation dates, and marks/CGPA.
    """
    education_records = []
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # First, find education section or search whole text
    for i, line in enumerate(lines):
        line_lower = line.lower()
        matched_degree = None
        for pattern, degree_name in DEGREE_PATTERNS:
            if re.search(pattern, line_lower):
                matched_degree = degree_name
                break

        if matched_degree:
            # Look at current line and surrounding 2 lines for year & college & CGPA
            context_block = " ".join(lines[max(0, i - 1) : min(len(lines), i + 3)])
            
            # Find year or year range
            start_year, end_year = None, None
            range_match = EDU_YEAR_RANGE_REGEX.search(context_block)
            if range_match:
                start_year = int(range_match.group(1))
                end_str = range_match.group(2).lower()
                end_year = None if end_str in ("present", "expected", "current") else int(end_str)
            else:
                single_year_match = SINGLE_YEAR_REGEX.search(context_block)
                if single_year_match:
                    end_year = int(single_year_match.group(1))

            # Find CGPA
            cgpa_match = CGPA_REGEX.search(context_block)
            cgpa = cgpa_match.group(1) if cgpa_match else None

            # Detect institution keyword
            inst_match = re.search(
                r"\b(?:university|institute|college|school|academy|iit|nit|bits|iiit|stanford|mit|oxford|harvard)\b[^\n,.]*",
                context_block,
                re.IGNORECASE,
            )
            institution = inst_match.group(0).strip() if inst_match else None

            # Deduplicate by degree name
            if not any(e["degree"] == matched_degree for e in education_records):
                education_records.append({
                    "degree": matched_degree,
                    "institution": institution,
                    "start_year": start_year,
                    "end_year": end_year,
                    "cgpa": cgpa,
                    "raw_context": context_block[:160],
                })

    return education_records


# ── Section Splitter ────────────────────────────────────────────────────────

SECTION_HEADERS = {
    "education": [r"^education\b", r"^academic\b", r"^qualifications\b"],
    "experience": [r"^work\s+experience\b", r"^experience\b", r"^employment\b", r"^professional\s+experience\b", r"^career\s+history\b"],
    "skills": [r"^technical\s+skills\b", r"^skills\b", r"^technologies\b", r"^core\s+competencies\b"],
    "projects": [r"^academic\s+projects\b", r"^projects\b", r"^key\s+projects\b"],
    "certifications": [r"^certifications\b", r"^licenses\b", r"^courses\b"],
    "references": [r"^references\b", r"^referees\b"],
}

def split_into_sections(text: str) -> Dict[str, str]:
    """
    Splits resume text into labeled sections based on standard headings.
    """
    sections: Dict[str, List[str]] = {"header": []}
    current_sec = "header"

    for line in text.split("\n"):
        clean_l = line.strip().lower()
        matched_sec = None

        if len(clean_l) <= 40:
            for sec_name, patterns in SECTION_HEADERS.items():
                if any(re.search(p, clean_l) for p in patterns):
                    matched_sec = sec_name
                    break

        if matched_sec:
            current_sec = matched_sec
            if current_sec not in sections:
                sections[current_sec] = []
        else:
            if current_sec not in sections:
                sections[current_sec] = []
            sections[current_sec].append(line)

    return {sec: "\n".join(lines).strip() for sec, lines in sections.items()}


def _parse_month_year(month_str: Optional[str], year_str: str) -> Tuple[int, int]:
    year = int(year_str)
    month = 1
    if month_str:
        clean_m = re.sub(r"[^\w]", "", month_str.lower())
        month = MONTH_MAP.get(clean_m, 1)
    return year, month


def extract_work_experience(text: str) -> List[Dict[str, Any]]:
    """
    Extracts candidate work history: companies, roles/titles, and date ranges.
    Scoped to the work experience section if present to avoid education date collisions.
    """
    sections = split_into_sections(text)
    # Target experience section specifically, or fallback to text if section not isolated
    target_text = sections.get("experience") or text
    lines = [l.strip() for l in target_text.split("\n") if l.strip()]
    now = datetime.now()

    experiences = []

    for i, line in enumerate(lines):
        date_match = DATE_RANGE_REGEX.search(line)
        if date_match:
            m1_str, y1_str, m2_str, y2_str = date_match.groups()
            start_year, start_month = _parse_month_year(m1_str, y1_str)

            is_current = y2_str.lower() in ("present", "current", "till date", "now")
            if is_current:
                end_year = now.year
                end_month = now.month
            else:
                end_year, end_month = _parse_month_year(m2_str, y2_str)

            duration_months = (end_year - start_year) * 12 + (end_month - start_month)
            duration_months = max(1, duration_months)

            # Search context lines: up to 2 lines before (for title/company) and 4 lines after (for tech/bullets)
            header_lines = lines[max(0, i - 2) : i + 1]
            desc_lines = lines[i : min(len(lines), i + 4)]
            context_lines = header_lines + desc_lines[1:]
            found_title = None
            company_candidate = None

            # Check if previous or current line has format: Role - Company or Role at Company
            for cl in header_lines:
                # Remove date substring if present
                clean_cl = DATE_RANGE_REGEX.sub("", cl).strip(" -–|,\t")
                if not clean_cl:
                    continue

                # Pattern: Title - Company or Title at Company or Title | Company
                split_match = re.split(r"\s+[-–|]\s+|\s+at\s+", clean_cl, flags=re.IGNORECASE)
                if len(split_match) >= 2:
                    p1, p2 = split_match[0].strip(), split_match[1].strip()
                    # Check which part looks like a job title
                    if any(t in p1.lower() for t in COMMON_JOB_TITLES):
                        found_title = p1.title()
                        company_candidate = p2
                        break
                    elif any(t in p2.lower() for t in COMMON_JOB_TITLES):
                        found_title = p2.title()
                        company_candidate = p1
                        break

                # If no delimiter, search for single title match
                if not found_title:
                    for title in COMMON_JOB_TITLES:
                        if re.search(rf"\b{re.escape(title)}\b", clean_cl, re.IGNORECASE):
                            found_title = title.title()
                            break

            experiences.append({
                "title": found_title or "Position / Role",
                "company": company_candidate or "Declared Company",
                "start_year": start_year,
                "start_month": start_month,
                "end_year": end_year,
                "end_month": end_month,
                "is_current": is_current,
                "duration_months": duration_months,
                "date_string": date_match.group(0),
                "raw_context": " ".join(context_lines)[:180],
            })

    # Sort experiences chronologically by start date
    experiences.sort(key=lambda x: (x["start_year"], x["start_month"]))
    return experiences



SKILL_CASING_MAP = {
    "go": "Go",
    "golang": "Go",
    "git": "Git",
    "aws": "AWS",
    "gcp": "GCP",
    "sql": "SQL",
    "nosql": "NoSQL",
    "html": "HTML",
    "css": "CSS",
    "ci/cd": "CI/CD",
    "c++": "C++",
    "c#": "C#",
    "php": "PHP",
    "ai": "AI",
    "ml": "ML",
    "api": "REST API",
    "rest api": "REST API",
}

def extract_skills(text: str) -> List[str]:
    """
    Extracts recognized technical skills and tools from resume text.
    """
    cleaned = text.lower()
    found_skills = []
    for skill in sorted(COMMON_SKILLS, key=len, reverse=True):
        pattern = rf"\b{re.escape(skill)}\b"
        if re.search(pattern, cleaned):
            if skill in SKILL_CASING_MAP:
                cased = SKILL_CASING_MAP[skill]
            elif len(skill) <= 3:
                cased = skill.upper()
            else:
                cased = skill.title()
            found_skills.append(cased)
    return list(dict.fromkeys(found_skills))


def extract_certifications(text: str) -> List[Dict[str, Any]]:
    """
    Extracts recognized certifications, accreditation IDs, and credentials.
    """
    certs = []
    cert_patterns = [
        (r"\b(?:aws\s+certified\s+[a-z\s]+|aws\s+solutions\s+architect)\b", "AWS Certification"),
        (r"\b(?:google\s+cloud\s+certified|gcp\s+professional)\b", "Google Cloud Certification"),
        (r"\b(?:certified\s+kubernetes\s+administrator|cka|ckad)\b", "Kubernetes (CKA/CKAD)"),
        (r"\b(?:pmp|project\s+management\s+professional)\b", "PMP Certification"),
        (r"\b(?:cissp|certified\s+information\s+systems\s+security\s+professional)\b", "CISSP Security"),
        (r"\b(?:ceh|certified\s+ethical\s+hacker)\b", "CEH Ethical Hacker"),
        (r"\b(?:microsoft\s+certified|azure\s+solutions\s+architect)\b", "Microsoft Azure Certification"),
        (r"\b(?:oracle\s+certified\s+professional|ocp)\b", "Oracle Certified"),
        (r"\b(?:scrum\s+master|csm|psm)\b", "Certified Scrum Master"),
    ]

    cleaned = text.lower()
    for pattern, name in cert_patterns:
        match = re.search(pattern, cleaned)
        if match:
            certs.append({
                "name": name,
                "matched_text": match.group(0).title(),
            })

    return certs


def extract_references(text: str) -> List[Dict[str, Any]]:
    """
    Extracts declared references, their reported names, titles, and contact emails.
    """
    references = []
    lines = text.split("\n")
    ref_section_idx = -1

    for i, line in enumerate(lines):
        if re.search(r"\b(?:references?|referees?)\b", line, re.IGNORECASE):
            ref_section_idx = i
            break

    if ref_section_idx != -1:
        ref_block = "\n".join(lines[ref_section_idx : min(len(lines), ref_section_idx + 15)])
        emails = EMAIL_REGEX.findall(ref_block)
        phones = PHONE_REGEX.findall(ref_block)

        # Detect referee names
        name_lines = []
        for l in ref_block.split("\n")[1:]:
            l_clean = l.strip()
            if l_clean and not EMAIL_REGEX.search(l_clean) and not PHONE_REGEX.search(l_clean):
                if len(l_clean.split()) in (2, 3, 4) and not any(w in l_clean.lower() for w in ["available", "upon", "request"]):
                    name_lines.append(l_clean)

        for idx, email in enumerate(emails):
            name = name_lines[idx] if idx < len(name_lines) else f"Reference #{idx+1}"
            phone = phones[idx] if idx < len(phones) else None
            references.append({
                "name": name,
                "email": email,
                "phone": phone.strip() if phone else None,
            })

    return references


# ── Unified Ingestion Pipeline ──────────────────────────────────────────────

def parse_resume(
    text: Optional[str] = None,
    file_bytes: Optional[bytes] = None,
    filename: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Ingests resume from raw text, PDF bytes, or image bytes and produces
    structured candidate metadata ready for fraud & timeline analysis.
    """
    source_type = "text"
    extracted_text = text or ""

    if file_bytes:
        fname = (filename or "").lower()
        if fname.endswith(".pdf"):
            source_type = "pdf"
            extracted_text = extract_text_from_pdf(file_bytes)
        elif fname.endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff")):
            source_type = "image"
            extracted_text = extract_text_from_image(file_bytes)
        else:
            # Attempt UTF-8 decode
            try:
                extracted_text = file_bytes.decode("utf-8")
                source_type = "text"
            except UnicodeDecodeError:
                # Try PDF fallback then OCR
                pdf_res = extract_text_from_pdf(file_bytes)
                if "[PDF_EXTRACTION_ERROR" not in pdf_res and len(pdf_res) > 30:
                    extracted_text = pdf_res
                    source_type = "pdf"
                else:
                    extracted_text = extract_text_from_image(file_bytes)
                    source_type = "image"

    contact = extract_contact_info(extracted_text)
    education = extract_education(extracted_text)
    experience = extract_work_experience(extracted_text)
    skills = extract_skills(extracted_text)
    certifications = extract_certifications(extracted_text)
    references = extract_references(extracted_text)

    # Compute overall career span in years
    total_experience_months = sum(e["duration_months"] for e in experience)
    total_experience_years = round(total_experience_months / 12.0, 1)

    return {
        "source_type": source_type,
        "char_count": len(extracted_text),
        "raw_text": extracted_text,
        "contact": contact,
        "education": education,
        "experience": experience,
        "total_experience_years": total_experience_years,
        "skills": skills,
        "certifications": certifications,
        "references": references,
    }
