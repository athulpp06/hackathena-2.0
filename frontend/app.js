// ============================================================
// LeakedIn — Frontend Application Logic
// ============================================================

const API_BASE = 'http://localhost:8000/api/v1';

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

// ── DOM References ─────────────────────────────────────────
const jobTextarea  = document.getElementById('job-text');
const companyInput = document.getElementById('company-name');
const emailInput   = document.getElementById('contact-email');
const analyzeBtn   = document.getElementById('analyze-btn');
const btnLabel     = document.getElementById('btn-label');
const btnSpinner   = document.getElementById('btn-spinner');
const resultsDiv   = document.getElementById('results');
const errorDiv     = document.getElementById('error-state');
const errorMsg     = document.getElementById('error-message');
const reanalyzeBtn = document.getElementById('reanalyze-btn');

// ── Event Listeners ────────────────────────────────────────
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

analyzeBtn.addEventListener('click', runAnalysis);

reanalyzeBtn.addEventListener('click', () => {
  resultsDiv.classList.add('hidden');
  errorDiv.classList.add('hidden');
  jobTextarea.value = '';
  companyInput.value = '';
  emailInput.value = '';
  jobTextarea.focus();
});

// ── Core Analysis Function ──────────────────────────────────
async function runAnalysis() {
  const text = jobTextarea.value.trim();
  if (!text || text.length < 30) {
    showError('Please paste a job description (at least 30 characters) to analyze.');
    return;
  }

  setLoading(true);
  resultsDiv.classList.add('hidden');
  errorDiv.classList.add('hidden');

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
    showError(`Could not reach the API server. Make sure it's running on http://localhost:8000\n\nDetails: ${err.message}`);
  } finally {
    setLoading(false);
  }
}

// ── Render Results ─────────────────────────────────────────
function renderResults(data, originalText) {
  // 1. Risk Gauge
  animateGauge(data.risk_score, data.risk_level);

  // 2. Score Breakdown Bars
  animateBar('ml-bar',     'ml-pct',     data.ml_score_pct);
  animateBar('rule-bar',   'rule-pct',   data.rule_penalty);
  animateBar('domain-bar', 'domain-pct', Math.min(100, (data.domain_flag_count / 3) * 100));

  // 3. Red Flags
  renderFlags([...data.red_flags, ...data.domain_flags.map(f => ({
    category:     f.type,
    severity:     f.severity,
    title:        f.title,
    matched_text: f.emails ? f.emails.join(', ') : '',
    explanation:  f.detail,
  }))]);

  // 4. Highlighted Text
  renderHighlightedText(originalText, data.highlighted_spans || []);

  // 5. Recommendations
  renderRecommendations(data.recommendations || []);

  // Show results
  resultsDiv.classList.remove('hidden');
  setTimeout(() => {
    resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, 100);
}

// ── Gauge Animation ────────────────────────────────────────
function animateGauge(score, level) {
  const gaugeScore = document.getElementById('gauge-score');
  const gaugeFill  = document.getElementById('gauge-fill');
  const riskBadge  = document.getElementById('risk-badge');
  const riskVerdict = document.getElementById('risk-verdict');

  // Arc length of the gauge track (calculated for the SVG path)
  const arcLength = 251.2;
  const offset = arcLength - (score / 100) * arcLength;

  const colorMap = {
    'Safe':       { stroke: '#22c55e', badge: 'badge-safe',     bg: 'rgba(34,197,94,0.15)',  border: 'rgba(34,197,94,0.4)'  },
    'Low Risk':   { stroke: '#f59e0b', badge: 'badge-low',      bg: 'rgba(245,158,11,0.15)', border: 'rgba(245,158,11,0.4)' },
    'Suspicious': { stroke: '#f97316', badge: 'badge-sus',      bg: 'rgba(249,115,22,0.15)', border: 'rgba(249,115,22,0.4)' },
    'High Risk':  { stroke: '#ef4444', badge: 'badge-high',     bg: 'rgba(239,68,68,0.15)',  border: 'rgba(239,68,68,0.4)'  },
  };
  const theme = colorMap[level] || colorMap['Suspicious'];

  // Animate score counter
  let current = 0;
  const step = score / 40;
  const interval = setInterval(() => {
    current = Math.min(current + step, score);
    gaugeScore.textContent = Math.round(current);
    if (current >= score) clearInterval(interval);
  }, 20);

  // Animate arc fill
  gaugeFill.style.strokeDashoffset = offset;
  gaugeFill.style.stroke = theme.stroke;
  gaugeFill.style.transition = 'stroke-dashoffset 1.2s cubic-bezier(0.22, 1, 0.36, 1), stroke 0.4s';

  // Badge
  riskBadge.textContent = level;
  riskBadge.style.background = theme.bg;
  riskBadge.style.border = `1px solid ${theme.border}`;
  riskBadge.style.color = theme.stroke;

  // Verdict (from API data)
  const verdictEl = document.getElementById('risk-verdict');
  verdictEl.textContent = '';
  setTimeout(() => {
    const verdictMap = {
      'Safe': 'No significant fraud signals detected. Always verify independently.',
      'Low Risk': 'Some minor anomalies found. Exercise caution and verify the company.',
      'Suspicious': 'Suspicious posting with multiple scam signals. Verify independently before proceeding.',
      'High Risk': 'Critical scam indicators detected. Do NOT respond or pay anything.',
    };
    verdictEl.textContent = verdictMap[level] || '';
  }, 200);
}

// ── Bar Animation ──────────────────────────────────────────
function animateBar(barId, pctId, value) {
  const pct = Math.min(100, Math.round(value));
  setTimeout(() => {
    document.getElementById(barId).style.width = `${pct}%`;
    document.getElementById(pctId).textContent = `${pct}%`;
  }, 300);
}

// ── Flag Rendering ─────────────────────────────────────────
function renderFlags(flags) {
  const container = document.getElementById('flags-list');
  const section   = document.getElementById('flags-section');
  container.innerHTML = '';

  if (!flags.length) {
    section.classList.add('hidden');
    return;
  }
  section.classList.remove('hidden');

  const sevOrder = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
  const sorted   = [...flags].sort((a, b) => (sevOrder[a.severity] ?? 9) - (sevOrder[b.severity] ?? 9));

  sorted.forEach((flag, i) => {
    const item = document.createElement('div');
    item.className = 'flag-item';
    item.style.animationDelay = `${i * 60}ms`;

    item.innerHTML = `
      <div class="flag-sev-dot sev-${flag.severity}"></div>
      <div class="flag-body">
        <div class="flag-title">
          ${escHtml(flag.title || flag.category)}
          <span class="flag-category-badge" style="${sevBadgeStyle(flag.severity)}">${flag.severity}</span>
        </div>
        ${flag.matched_text ? `<div class="flag-matched">${escHtml(flag.matched_text)}</div>` : ''}
        <div class="flag-explanation">${escHtml(flag.explanation || flag.detail || '')}</div>
      </div>
    `;
    container.appendChild(item);
  });
}

// ── Text Highlighter ───────────────────────────────────────
function renderHighlightedText(text, spans) {
  const container = document.getElementById('highlighted-text');
  const section   = document.getElementById('highlight-section');

  if (!spans.length) {
    section.classList.add('hidden');
    return;
  }
  section.classList.remove('hidden');

  // Sort spans by start position
  const sorted = [...spans].sort((a, b) => a.start - b.start);

  let html = '';
  let cursor = 0;

  for (const span of sorted) {
    const start = Math.min(span.start, text.length);
    const end   = Math.min(span.end, text.length);
    if (start > cursor) {
      html += escHtml(text.slice(cursor, start));
    }
    if (end > start) {
      html += `<mark class="hl-${span.severity}">${escHtml(text.slice(start, end))}</mark>`;
    }
    cursor = end;
  }
  if (cursor < text.length) {
    html += escHtml(text.slice(cursor));
  }

  container.innerHTML = html;
}

// ── Recommendations ────────────────────────────────────────
function renderRecommendations(recs) {
  const list    = document.getElementById('recs-list');
  const section = document.getElementById('recs-section');
  list.innerHTML = '';

  if (!recs.length) { section.classList.add('hidden'); return; }
  section.classList.remove('hidden');

  recs.forEach(r => {
    const li = document.createElement('li');
    li.textContent = r;
    list.appendChild(li);
  });
}

// ── UI Helpers ─────────────────────────────────────────────
function setLoading(isLoading) {
  analyzeBtn.disabled = isLoading;
  btnLabel.textContent = isLoading ? 'Analyzing...' : '🔍 Analyze Job Posting';
  btnSpinner.classList.toggle('hidden', !isLoading);
}

function showError(message) {
  errorMsg.textContent = message;
  errorDiv.classList.remove('hidden');
  resultsDiv.classList.add('hidden');
  errorDiv.scrollIntoView({ behavior: 'smooth' });
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function sevBadgeStyle(severity) {
  const styles = {
    CRITICAL: 'background:rgba(239,68,68,0.15);color:#ef4444;border:1px solid rgba(239,68,68,0.3)',
    HIGH:     'background:rgba(249,115,22,0.15);color:#f97316;border:1px solid rgba(249,115,22,0.3)',
    MEDIUM:   'background:rgba(245,158,11,0.15);color:#f59e0b;border:1px solid rgba(245,158,11,0.3)',
    LOW:      'background:rgba(34,197,94,0.15);color:#22c55e;border:1px solid rgba(34,197,94,0.3)',
  };
  return styles[severity] || styles.LOW;
}
