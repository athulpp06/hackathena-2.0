// ============================================================
// LeakedIn — Frontend Application Logic
// Supports: Raw Text, Uploaded Images, and Direct Clipboard Screenshots
// ============================================================

const API_BASE = '/api/v1';

// Sample job postings for demo
const SAMPLE_SCAM = `URGENT HIRING: Data Entry Operator at TCS (Tata Consultancy Services)

Job Description:
We are urgently hiring 50 data entry operators for our new home-based division. This is a fully remote work from home opportunity with immediate joining.

Salary: Earn Rs 45,000 per week working only 2-3 hours per day. Weekly payments guaranteed directly to your bank account.

Requirements: No experience required. No educational qualification required. No interview needed — direct selection for all applicants.

Benefits: Flexible hours, work from anywhere, immediate joining bonus of Rs 5,000.

IMPORTANT: Only 3 seats left. Offer expires within 24 hours. Act fast!

To confirm your slot: A refundable security deposit of Rs 1,500 is required for your training kit and login credentials. Pay via PhonePe or Google Pay and your amount will be refunded within 48 hours of joining.

Send your CV on WhatsApp: +91 98765 43210
Contact: hr.tcs.recruiter@gmail.com

Apply NOW — This offer will not last long!`;

const SAMPLE_REAL = `Senior Backend Engineer — Cloud Platform Team
Company: Stripe (stripe.com)
Location: Bangalore, India (Hybrid) | Full-Time

About Stripe:
Stripe is a technology company that builds economic infrastructure for the internet. Businesses of every size—from new startups to public companies like Amazon, Google, and Salesforce—use Stripe's software and APIs to accept payments, send payouts, and manage their businesses online.

Role Overview:
We are looking for a Senior Backend Engineer to join our Cloud Platform team. You will design, build, and maintain the distributed systems that power Stripe's core payment infrastructure, handling millions of transactions per day.

Responsibilities:
- Design and implement high-throughput, fault-tolerant REST and gRPC microservices.
- Own large, complex systems and drive them from design to production.
- Collaborate cross-functionally with product, design, and data teams.
- Participate in on-call rotations for the systems you build.
- Mentor junior engineers through code reviews and technical discussions.

Requirements:
- 4+ years of software engineering experience.
- Proficiency in Go, Python, or Ruby; familiarity with distributed systems.
- Experience with relational databases (MySQL, PostgreSQL) and caching layers (Redis).
- Strong understanding of system design, networking, and security principles.
- Bachelor's degree in Computer Science or equivalent practical experience.

Compensation & Benefits:
- Competitive base salary (₹45–65 LPA range, DOE).
- Equity (RSUs) with 4-year vest and 1-year cliff.
- Comprehensive health insurance for employee and dependents.
- 25 days paid time off + company holidays.
- Annual learning & development budget of $2,000.
- Home office setup allowance.

To Apply:
Submit your resume and portfolio via our official careers portal: https://stripe.com/jobs
For questions, contact our recruiting team at recruiting@stripe.com`;

// ── State ───────────────────────────────────────────────────
let currentMode = 'text'; // 'text' | 'image'
let currentImageFile = null;

// ── DOM References ─────────────────────────────────────────
const tabText        = document.getElementById('tab-text');
const tabImage       = document.getElementById('tab-image');
const panelText      = document.getElementById('panel-text');
const panelImage     = document.getElementById('panel-image');

const jobTextarea    = document.getElementById('job-text');
const companyInput   = document.getElementById('company-name');
const emailInput     = document.getElementById('contact-email');

const dropZone       = document.getElementById('drop-zone');
const fileInput      = document.getElementById('file-input');
const dropPrompt     = document.getElementById('drop-prompt');
const dropPreview    = document.getElementById('drop-preview');
const previewImg     = document.getElementById('preview-img');
const previewFilename= document.getElementById('preview-filename');
const removeImgBtn   = document.getElementById('remove-img-btn');

const ocrStatusCard  = document.getElementById('ocr-status-card');
const ocrStatusText  = document.getElementById('ocr-status-text');
const ocrExtractedCard = document.getElementById('ocr-extracted-card');
const ocrExtractedText = document.getElementById('ocr-extracted-text');
const ocrCharCount   = document.getElementById('ocr-char-count');
const ocrEngineBadge = document.getElementById('ocr-engine-badge');

const analyzeBtn     = document.getElementById('analyze-btn');
const btnLabel       = document.getElementById('btn-label');
const btnSpinner     = document.getElementById('btn-spinner');
const resultsDiv     = document.getElementById('results');
const errorDiv       = document.getElementById('error-state');
const errorMsg       = document.getElementById('error-message');
const reanalyzeBtn   = document.getElementById('reanalyze-btn');

// ── Mode Tabs ──────────────────────────────────────────────
function switchMode(mode) {
  currentMode = mode;
  if (mode === 'text') {
    tabText.classList.add('active');
    tabImage.classList.remove('active');
    panelText.classList.remove('hidden');
    panelImage.classList.add('hidden');
  } else {
    tabImage.classList.add('active');
    tabText.classList.remove('active');
    panelImage.classList.remove('hidden');
    panelText.classList.add('hidden');
  }
}

tabText.addEventListener('click', () => switchMode('text'));
tabImage.addEventListener('click', () => switchMode('image'));

// ── Text Mode Sample Buttons ───────────────────────────────
document.getElementById('load-scam').addEventListener('click', () => {
  jobTextarea.value = SAMPLE_SCAM;
  companyInput.value = 'TCS';
  emailInput.value = '';
  jobTextarea.focus();
});

document.getElementById('load-real').addEventListener('click', () => {
  jobTextarea.value = SAMPLE_REAL;
  companyInput.value = 'Stripe';
  emailInput.value = 'recruiting@stripe.com';
  jobTextarea.focus();
});

// ── Image Mode Sample Buttons ──────────────────────────────
async function loadSampleImage(url, filename, company) {
  switchMode('image');
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error('Could not load sample image');
    const blob = await res.blob();
    const file = new File([blob], filename, { type: blob.type || 'image/png' });
    companyInput.value = company;
    emailInput.value = '';
    handleFileSelect(file);
  } catch (err) {
    showError(`Error loading sample screenshot: ${err.message}`);
  }
}

document.getElementById('load-scam-img').addEventListener('click', () => {
  loadSampleImage('/samples/scam_job_offer.png', 'scam_job_offer.png', 'TCS');
});

document.getElementById('load-real-img').addEventListener('click', () => {
  loadSampleImage('/samples/legit_job_offer.png', 'legit_job_offer.png', 'Stripe');
});

// ── Drop Zone & File Selection ─────────────────────────────
dropZone.addEventListener('click', (e) => {
  if (e.target !== removeImgBtn && !removeImgBtn.contains(e.target)) {
    fileInput.click();
  }
});

fileInput.addEventListener('change', (e) => {
  if (e.target.files && e.target.files[0]) {
    handleFileSelect(e.target.files[0]);
  }
});

dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
  dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  if (e.dataTransfer.files && e.dataTransfer.files[0]) {
    handleFileSelect(e.dataTransfer.files[0]);
  }
});

// Global Paste: Capture Ctrl+V screenshot anywhere
window.addEventListener('paste', (e) => {
  const items = e.clipboardData?.items;
  if (!items) return;
  for (const item of items) {
    if (item.type.indexOf('image') !== -1) {
      const blob = item.getAsFile();
      switchMode('image');
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const file = new File([blob], `screenshot-${timestamp}.png`, { type: blob.type });
      handleFileSelect(file);
      break;
    }
  }
});

function handleFileSelect(file) {
  if (!file || !file.type.startsWith('image/')) {
    showError('Please upload a valid image file (PNG, JPEG, WebP, BMP, TIFF).');
    return;
  }

  currentImageFile = file;

  // Show preview
  const reader = new FileReader();
  reader.onload = (e) => {
    previewImg.src = e.target.result;
    previewFilename.textContent = `${file.name} (${Math.round(file.size / 1024)} KB)`;
    dropPrompt.classList.add('hidden');
    dropPreview.classList.remove('hidden');
    errorDiv.classList.add('hidden');
  };
  reader.readAsDataURL(file);

  // Reset previously extracted text
  ocrExtractedCard.classList.add('hidden');
  ocrStatusCard.classList.remove('hidden');
  ocrStatusText.textContent = 'Screenshot loaded. Click "Analyze Job Posting" to extract text and detect fraud.';
}

removeImgBtn.addEventListener('click', (e) => {
  e.stopPropagation();
  currentImageFile = null;
  fileInput.value = '';
  previewImg.src = '';
  dropPreview.classList.add('hidden');
  dropPrompt.classList.remove('hidden');
  ocrStatusCard.classList.add('hidden');
  ocrExtractedCard.classList.add('hidden');
});

// ── Core Analysis Flow ──────────────────────────────────────
analyzeBtn.addEventListener('click', runAnalysis);

reanalyzeBtn.addEventListener('click', () => {
  resultsDiv.classList.add('hidden');
  errorDiv.classList.add('hidden');
  if (currentMode === 'text') {
    jobTextarea.focus();
  }
});

async function runAnalysis() {
  errorDiv.classList.add('hidden');
  resultsDiv.classList.add('hidden');

  if (currentMode === 'text') {
    const text = jobTextarea.value.trim();
    if (!text || text.length < 30) {
      showError('Please paste a job description (at least 30 characters) to analyze.');
      return;
    }

    setLoading(true, 'Analyzing text with AI models...');
    try {
      const response = await fetch(`${API_BASE}/analyse-job`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text,
          company_name: companyInput.value.trim(),
          contact_email: emailInput.value.trim(),
        }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || `API error ${response.status}`);
      }

      const data = await response.json();
      renderResults(data, text);
    } catch (err) {
      showError(`Analysis failed: ${err.message}`);
    } finally {
      setLoading(false);
    }

  } else {
    // Image / Screenshot Mode
    if (!currentImageFile) {
      showError('Please upload an image, drop a screenshot, or press Ctrl+V to paste one first.');
      return;
    }

    setLoading(true, 'Extracting text with OCR and scanning for scam signals...');
    ocrStatusCard.classList.remove('hidden');
    ocrStatusText.textContent = 'Running Optical Character Recognition (OCR)...';

    const formData = new FormData();
    formData.append('file', currentImageFile);
    if (companyInput.value.trim()) {
      formData.append('company_name', companyInput.value.trim());
    }
    if (emailInput.value.trim()) {
      formData.append('contact_email', emailInput.value.trim());
    }

    try {
      const response = await fetch(`${API_BASE}/analyse-image`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || `API error ${response.status}`);
      }

      const data = await response.json();

      // Show extracted text card in panel
      if (data.ocr_extracted_text) {
        ocrExtractedCard.classList.remove('hidden');
        ocrExtractedText.value = data.ocr_extracted_text;
        ocrCharCount.textContent = data.ocr_char_count || data.ocr_extracted_text.length;
        ocrEngineBadge.textContent = `${data.ocr_engine || 'OCR'} (${Math.round((data.ocr_confidence || 0.85) * 100)}% conf)`;
      }

      ocrStatusCard.classList.remove('hidden');
      ocrStatusText.textContent = `Text extracted successfully via ${data.ocr_engine || 'OCR'}.`;

      renderResults(data, data.ocr_extracted_text || '');
    } catch (err) {
      showError(`Image analysis failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }
}

// ── Render Results ─────────────────────────────────────────
function renderResults(data, analyzedText) {
  // 1. Risk Gauge
  animateGauge(data.risk_score, data.risk_level, data.verdict);

  // 2. Score Breakdown Bars
  animateBar('ml-bar',     'ml-pct',     data.ml_score_pct);
  animateBar('rule-bar',   'rule-pct',   data.rule_penalty);
  animateBar('domain-bar', 'domain-pct', Math.min(100, (data.domain_flag_count / 3) * 100));

  // 3. Red Flags
  const allFlags = [
    ...(data.red_flags || []),
    ...(data.domain_flags || []).map(f => ({
      category:     f.type,
      severity:     f.severity,
      title:        f.title,
      matched_text: f.emails ? f.emails.join(', ') : '',
      explanation:  f.detail,
    }))
  ];
  renderFlags(allFlags);

  // 4. Highlighted Text
  renderHighlightedText(analyzedText, data.highlighted_spans || []);

  // 5. Recommendations
  renderRecommendations(data.recommendations || []);

  // Show results
  resultsDiv.classList.remove('hidden');
  setTimeout(() => {
    resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, 100);
}

// ── Gauge Animation ────────────────────────────────────────
function animateGauge(score, level, apiVerdict) {
  const gaugeScore = document.getElementById('gauge-score');
  const gaugeFill  = document.getElementById('gauge-fill');
  const riskBadge  = document.getElementById('risk-badge');
  const riskVerdict = document.getElementById('risk-verdict');

  const arcLength = 251.2;
  const offset = arcLength - (score / 100) * arcLength;

  const colorMap = {
    'Safe':       { stroke: '#22c55e', bg: 'rgba(34,197,94,0.15)',  border: 'rgba(34,197,94,0.4)'  },
    'Low Risk':   { stroke: '#f59e0b', bg: 'rgba(245,158,11,0.15)', border: 'rgba(245,158,11,0.4)' },
    'Suspicious': { stroke: '#f97316', bg: 'rgba(249,115,22,0.15)', border: 'rgba(249,115,22,0.4)' },
    'High Risk':  { stroke: '#ef4444', bg: 'rgba(239,68,68,0.15)',  border: 'rgba(239,68,68,0.4)'  },
  };
  const theme = colorMap[level] || colorMap['Suspicious'];

  let current = 0;
  const step = Math.max(1, score / 40);
  const interval = setInterval(() => {
    current = Math.min(current + step, score);
    gaugeScore.textContent = Math.round(current);
    if (current >= score) clearInterval(interval);
  }, 20);

  gaugeFill.style.strokeDashoffset = offset;
  gaugeFill.style.stroke = theme.stroke;
  gaugeFill.style.transition = 'stroke-dashoffset 1.2s cubic-bezier(0.22, 1, 0.36, 1), stroke 0.4s';

  riskBadge.textContent = level;
  riskBadge.style.background = theme.bg;
  riskBadge.style.border = `1px solid ${theme.border}`;
  riskBadge.style.color = theme.stroke;

  riskVerdict.textContent = apiVerdict || '';
}

// ── Bar Animation ──────────────────────────────────────────
function animateBar(barId, pctId, value) {
  const pct = Math.min(100, Math.round(value || 0));
  setTimeout(() => {
    const bar = document.getElementById(barId);
    const label = document.getElementById(pctId);
    if (bar) bar.style.width = `${pct}%`;
    if (label) label.textContent = `${pct}%`;
  }, 300);
}

// ── Flag Rendering ─────────────────────────────────────────
function renderFlags(flags) {
  const container = document.getElementById('flags-list');
  const section   = document.getElementById('flags-section');
  container.innerHTML = '';

  if (!flags || !flags.length) {
    section.classList.add('hidden');
    return;
  }
  section.classList.remove('hidden');

  const sevOrder = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
  const sorted   = [...flags].sort((a, b) => (sevOrder[a.severity] ?? 9) - (sevOrder[b.severity] ?? 9));

  sorted.forEach((flag) => {
    const item = document.createElement('div');
    item.className = 'flag-item';

    const sevColors = {
      CRITICAL: { bg: 'rgba(239,68,68,0.15)',   border: 'rgba(239,68,68,0.3)',   color: '#f87171' },
      HIGH:     { bg: 'rgba(249,115,22,0.15)',  border: 'rgba(249,115,22,0.3)',  color: '#fb923c' },
      MEDIUM:   { bg: 'rgba(245,158,11,0.15)',  border: 'rgba(245,158,11,0.3)',  color: '#fbbf24' },
      LOW:      { bg: 'rgba(59,130,246,0.15)',   border: 'rgba(59,130,246,0.3)',   color: '#60a5fa' },
    };
    const c = sevColors[flag.severity] || sevColors.MEDIUM;

    item.innerHTML = `
      <div class="flag-top">
        <span class="flag-badge" style="background:${c.bg}; border:1px solid ${c.border}; color:${c.color}">
          ${flag.severity}
        </span>
        <span class="flag-title">${escapeHtml(flag.title || flag.category || 'Warning')}</span>
      </div>
      ${flag.matched_text ? `<div class="flag-match">"${escapeHtml(flag.matched_text)}"</div>` : ''}
      <div class="flag-desc">${escapeHtml(flag.explanation || flag.detail || '')}</div>
    `;
    container.appendChild(item);
  });
}

// ── Highlighted Text Rendering ─────────────────────────────
function renderHighlightedText(text, spans) {
  const container = document.getElementById('highlighted-text');
  const section   = document.getElementById('highlight-section');

  if (!spans || !spans.length || !text) {
    section.classList.add('hidden');
    return;
  }
  section.classList.remove('hidden');

  const sortedSpans = [...spans].sort((a, b) => a.start - b.start);
  let html = '';
  let lastIndex = 0;

  sortedSpans.forEach(span => {
    const start = Math.max(0, span.start);
    const end   = Math.min(text.length, span.end);

    if (start < lastIndex) return; // Skip overlapping spans

    html += escapeHtml(text.slice(lastIndex, start));

    const chunk = escapeHtml(text.slice(start, end));
    const sev = (span.severity || 'HIGH').toLowerCase();
    html += `<mark class="highlight-${sev}" title="${escapeHtml(span.title || span.severity || 'Scam Signal')}">${chunk}</mark>`;

    lastIndex = end;
  });

  html += escapeHtml(text.slice(lastIndex));
  container.innerHTML = html.replace(/\n/g, '<br>');
}

// ── Recommendations ─────────────────────────────────────────
function renderRecommendations(recs) {
  const list    = document.getElementById('recs-list');
  const section = document.getElementById('recs-section');
  list.innerHTML = '';

  if (!recs || !recs.length) {
    section.classList.add('hidden');
    return;
  }
  section.classList.remove('hidden');

  recs.forEach(rec => {
    const li = document.createElement('li');
    li.textContent = rec;
    list.appendChild(li);
  });
}

// ── Helpers ────────────────────────────────────────────────
function setLoading(loading, message = 'Analyzing Job Posting...') {
  analyzeBtn.disabled = loading;
  if (loading) {
    btnLabel.textContent = message;
    btnSpinner.classList.remove('hidden');
  } else {
    btnLabel.textContent = '🔍 Analyze Job Posting';
    btnSpinner.classList.add('hidden');
  }
}

function showError(msg) {
  errorMsg.textContent = msg;
  errorDiv.classList.remove('hidden');
  errorDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
