/**
 * LeakedIn Chrome Extension — Content Script (Manifest V3)
 *
 * Security:
 * - 100% textContent and DOM API only. Zero innerHTML.
 * - Scans happen ONLY on user click. Zero background auto-scanning.
 * - All network calls are dispatched via background service worker.
 */

(function () {
  if (window.__leakedinInjected) return;
  window.__leakedinInjected = true;

  // Potential selectors for job descriptions across major portals
  const JOB_CONTAINER_SELECTORS = [
    // LinkedIn
    ".jobs-description__content",
    ".jobs-description-content__text",
    ".jobs-box__html-content",
    ".job-view-layout",
    "[data-job-id] .jobs-description",
    ".jobs-search__job-details--container",
    ".job-details-jobs-unified-top-card__content--two-pane",
    // Indeed
    "#jobDescriptionText",
    ".jobsearch-jobDescriptionText",
    "#jobDescriptionSection",
    "[data-testid='jobsearch-JobComponent-description']",
    // Naukri
    ".styles_job-desc-container__txpYf",
    ".job-desc",
    ".dang-inner-html",
    ".jd-description",
    "[class*='job-desc']",
    // Generic semantic fallbacks
    "article[class*='job']",
    "main [class*='description']",
    "article",
    "main"
  ];

  /**
   * Attempts to locate the job description container on the page
   */
  function extractJobDescription() {
    for (const sel of JOB_CONTAINER_SELECTORS) {
      try {
        const el = document.querySelector(sel);
        if (el) {
          const text = (el.innerText || el.textContent || "").trim();
          if (text.length >= 80) {
            return text;
          }
        }
      } catch (_) {
        // Continue to next selector
      }
    }

    // Fallback: active text selection
    const selection = window.getSelection() ? window.getSelection().toString().trim() : "";
    if (selection && selection.length >= 20) {
      return selection;
    }

    return null;
  }

  // ---------------------------------------------------------------------------
  // Floating "Check this job" Button
  // ---------------------------------------------------------------------------
  const floatingBtn = document.createElement("button");
  floatingBtn.id = "leakedin-floating-trigger";
  floatingBtn.type = "button";

  const btnIcon = document.createElement("span");
  btnIcon.textContent = "🛡️";
  btnIcon.style.fontSize = "16px";

  const btnText = document.createElement("span");
  btnText.textContent = "Check this job";
  btnText.id = "leakedin-btn-label";

  floatingBtn.appendChild(btnIcon);
  floatingBtn.appendChild(btnText);

  floatingBtn.style.cssText = `
    position: fixed !important;
    bottom: 24px !important;
    right: 24px !important;
    z-index: 2147483646 !important;
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.25) !important;
    border-radius: 9999px !important;
    padding: 10px 18px !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    cursor: pointer !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease !important;
  `;

  floatingBtn.addEventListener("mouseenter", () => {
    floatingBtn.style.transform = "translateY(-2px) scale(1.02)";
    floatingBtn.style.boxShadow = "0 8px 24px rgba(79, 70, 229, 0.5)";
  });
  floatingBtn.addEventListener("mouseleave", () => {
    floatingBtn.style.transform = "translateY(0) scale(1)";
    floatingBtn.style.boxShadow = "0 4px 20px rgba(0, 0, 0, 0.4)";
  });

  document.body.appendChild(floatingBtn);

  // ---------------------------------------------------------------------------
  // In-Page Result Modal (Strictly DOM node creation, zero innerHTML)
  // ---------------------------------------------------------------------------
  let modalContainer = null;

  function closeResultModal() {
    if (modalContainer && modalContainer.parentNode) {
      modalContainer.parentNode.removeChild(modalContainer);
      modalContainer = null;
    }
  }

  function renderInPageModal(scanResult, userWarning) {
    closeResultModal();

    modalContainer = document.createElement("div");
    modalContainer.id = "leakedin-modal-container";
    modalContainer.style.cssText = `
      position: fixed !important;
      bottom: 80px !important;
      right: 24px !important;
      z-index: 2147483647 !important;
      width: 360px !important;
      max-width: calc(100vw - 48px) !important;
      max-height: 520px !important;
      overflow-y: auto !important;
      background: #0f172a !important;
      color: #f8fafc !important;
      border: 1px solid #334155 !important;
      border-radius: 14px !important;
      padding: 16px !important;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
      box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6) !important;
      display: flex !important;
      flex-direction: column !important;
      gap: 12px !important;
      animation: leakedin-fade-in 0.2s ease !important;
    `;

    // Header Bar
    const header = document.createElement("div");
    header.style.cssText = "display: flex; justify-content: space-between; align-items: center;";

    const headerTitleBox = document.createElement("div");
    headerTitleBox.style.cssText = "display: flex; align-items: center; gap: 8px;";

    const headerIcon = document.createElement("img");
    headerIcon.src = chrome.runtime.getURL("icons/icon32.png");
    headerIcon.alt = "LeakedIn";
    headerIcon.style.cssText = "width: 18px; height: 18px; border-radius: 4px; vertical-align: middle;";

    const headerTitle = document.createElement("strong");
    headerTitle.textContent = "LeakedIn Analysis";
    headerTitle.style.cssText = "font-size: 15px; color: #ffffff;";

    headerTitleBox.appendChild(headerIcon);
    headerTitleBox.appendChild(headerTitle);

    const closeBtn = document.createElement("button");
    closeBtn.textContent = "✕";
    closeBtn.type = "button";
    closeBtn.style.cssText = `
      background: none;
      border: none;
      color: #94a3b8;
      cursor: pointer;
      font-size: 16px;
      padding: 2px 6px;
      border-radius: 4px;
    `;
    closeBtn.addEventListener("click", closeResultModal);

    header.appendChild(headerTitleBox);
    header.appendChild(closeBtn);
    modalContainer.appendChild(header);

    // Optional truncation warning
    if (userWarning) {
      const warnBox = document.createElement("div");
      warnBox.style.cssText = "font-size: 11px; background: rgba(245, 158, 11, 0.15); color: #fbbf24; padding: 6px 8px; border-radius: 6px;";
      warnBox.textContent = `ℹ️ ${userWarning}`;
      modalContainer.appendChild(warnBox);
    }

    // --- CASE 1: Connection or Validation Error ---
    if (!scanResult || !scanResult.success) {
      const errBox = document.createElement("div");
      errBox.style.cssText = "background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 12px;";

      const errTitle = document.createElement("strong");
      errTitle.textContent = "⚠️ Scan Failed";
      errTitle.style.cssText = "display: block; font-size: 13px; color: #ef4444; margin-bottom: 4px;";

      const errText = document.createElement("p");
      errText.textContent = scanResult?.error || "Unable to contact LeakedIn API. Is http://localhost:8000 running?";
      errText.style.cssText = "font-size: 12px; color: #cbd5e1; margin: 0; line-height: 1.4;";

      errBox.appendChild(errTitle);
      errBox.appendChild(errText);
      modalContainer.appendChild(errBox);

      document.body.appendChild(modalContainer);
      return;
    }

    const data = scanResult.data;

    // --- CASE 2: Gatekeeper Rejection (Not a job posting) ---
    if (data.is_job_posting === false) {
      const gkBox = document.createElement("div");
      gkBox.style.cssText = "background: rgba(100, 116, 139, 0.2); border: 1px solid #475569; border-radius: 8px; padding: 12px;";

      const gkTtl = document.createElement("strong");
      gkTtl.textContent = "⚠️ This doesn't look like a job posting";
      gkTtl.style.cssText = "display: block; font-size: 13px; color: #f1f5f9; margin-bottom: 6px;";

      const gkDesc = document.createElement("p");
      gkDesc.textContent = data.gatekeeper_reasoning || data.verdict || "The submitted content does not match standard recruitment advertisement patterns. Fraud analysis was withheld.";
      gkDesc.style.cssText = "font-size: 12px; color: #94a3b8; margin: 0; line-height: 1.4;";

      gkBox.appendChild(gkTtl);
      gkBox.appendChild(gkDesc);
      modalContainer.appendChild(gkBox);

      document.body.appendChild(modalContainer);
      return;
    }

    // --- CASE 3: Active Job Posting Analysis ---
    const score = Math.max(0, Math.min(100, Math.round(Number(data.risk_score) || 0)));
    let scoreColor = "#10b981"; // Safe (0-25)
    if (score > 75) {
      scoreColor = "#ef4444"; // High (76-100)
    } else if (score > 50) {
      scoreColor = "#f97316"; // Suspicious (51-75)
    } else if (score > 25) {
      scoreColor = "#f59e0b"; // Low (26-50)
    }

    // Score Header Card
    const scoreCard = document.createElement("div");
    scoreCard.style.cssText = "display: flex; align-items: center; gap: 12px; background: rgba(255, 255, 255, 0.04); padding: 10px 12px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.08);";

    const scoreCircle = document.createElement("div");
    scoreCircle.textContent = String(score);
    scoreCircle.style.cssText = `
      width: 46px;
      height: 46px;
      border-radius: 50%;
      border: 3px solid ${scoreColor};
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 17px;
      color: ${scoreColor};
      flex-shrink: 0;
    `;

    const metaBox = document.createElement("div");

    const levelText = document.createElement("div");
    levelText.textContent = data.risk_level || "Unknown";
    levelText.style.cssText = `font-weight: 700; font-size: 14px; color: ${scoreColor};`;

    const verdictText = document.createElement("div");
    verdictText.textContent = data.verdict || "";
    verdictText.style.cssText = "font-size: 11px; color: #94a3b8; line-height: 1.3; margin-top: 2px;";

    metaBox.appendChild(levelText);
    metaBox.appendChild(verdictText);
    scoreCard.appendChild(scoreCircle);
    scoreCard.appendChild(metaBox);
    modalContainer.appendChild(scoreCard);

    // Red Flags List
    const redFlags = data.red_flags || [];
    if (redFlags.length > 0) {
      const rfSec = document.createElement("div");

      const rfTitle = document.createElement("div");
      rfTitle.textContent = `🚩 Red Flags (${redFlags.length}):`;
      rfTitle.style.cssText = "font-size: 12px; font-weight: 600; color: #fca5a5; margin-bottom: 6px;";
      rfSec.appendChild(rfTitle);

      const rfList = document.createElement("div");
      rfList.style.cssText = "display: flex; flex-direction: column; gap: 4px; max-height: 110px; overflow-y: auto;";

      redFlags.slice(0, 3).forEach((f) => {
        const item = document.createElement("div");
        item.style.cssText = "font-size: 11px; background: rgba(239, 68, 68, 0.12); border-left: 3px solid #ef4444; padding: 4px 8px; border-radius: 4px; color: #fecaca;";

        const titleSpan = document.createElement("strong");
        titleSpan.textContent = `[${f.severity || "FLAG"}] ${f.title || f.category || "Red Flag"}: `;

        const matchSpan = document.createElement("span");
        matchSpan.textContent = f.matched_text ? `"${f.matched_text}"` : (f.explanation || f.message || "");

        item.appendChild(titleSpan);
        item.appendChild(matchSpan);
        rfList.appendChild(item);
      });

      rfSec.appendChild(rfList);
      modalContainer.appendChild(rfSec);
    }

    // Domain Flags List
    const domainFlags = data.domain_flags || [];
    if (domainFlags.length > 0) {
      const dfSec = document.createElement("div");

      const dfTitle = document.createElement("div");
      dfTitle.textContent = `🌐 Domain Alerts (${domainFlags.length}):`;
      dfTitle.style.cssText = "font-size: 12px; font-weight: 600; color: #fde047; margin-bottom: 6px;";
      dfSec.appendChild(dfTitle);

      domainFlags.slice(0, 2).forEach((df) => {
        const item = document.createElement("div");
        item.style.cssText = "font-size: 11px; background: rgba(234, 179, 8, 0.12); border-left: 3px solid #eab308; padding: 4px 8px; border-radius: 4px; color: #fef08a; margin-bottom: 4px;";

        const ttl = document.createElement("strong");
        ttl.textContent = `${df.title || "Domain Alert"}: `;

        const det = document.createElement("span");
        det.textContent = df.detail || "";

        item.appendChild(ttl);
        item.appendChild(det);
        dfSec.appendChild(item);
      });

      modalContainer.appendChild(dfSec);
    }

    // First Recommendation
    const recs = data.recommendations || [];
    if (recs.length > 0 && recs[0]) {
      const recBox = document.createElement("div");
      recBox.style.cssText = "font-size: 11px; color: #cbd5e1; background: rgba(255, 255, 255, 0.03); padding: 8px; border-radius: 6px; border: 1px solid rgba(255, 255, 255, 0.05);";

      const recLabel = document.createElement("strong");
      recLabel.textContent = "💡 Advice: ";
      recLabel.style.color = "#38bdf8";

      const recText = document.createElement("span");
      recText.textContent = recs[0];

      recBox.appendChild(recLabel);
      recBox.appendChild(recText);
      modalContainer.appendChild(recBox);
    }

    // 1930 Cybercrime Helpline Notice (For High Risk only)
    if (data.risk_level === "High Risk" || score >= 76) {
      const helpBox = document.createElement("div");
      helpBox.style.cssText = "font-size: 11px; background: rgba(239, 68, 68, 0.2); border: 1px solid #ef4444; color: #fee2e2; padding: 8px; border-radius: 6px;";

      const helpStrong = document.createElement("strong");
      helpStrong.textContent = "🚨 1930 Cybercrime Helpline: ";
      helpStrong.style.color = "#f87171";

      const helpText = document.createElement("span");
      helpText.textContent = "If money was transferred or government IDs were shared, dial 1930 immediately or file an incident at cybercrime.gov.in.";

      helpBox.appendChild(helpStrong);
      helpBox.appendChild(helpText);
      modalContainer.appendChild(helpBox);
    }

    document.body.appendChild(modalContainer);
  }

  // ---------------------------------------------------------------------------
  // Floating Button Event Listener (Scans ONLY on explicit click)
  // ---------------------------------------------------------------------------
  floatingBtn.addEventListener("click", () => {
    const jobText = extractJobDescription();

    if (!jobText || jobText.length < 15) {
      renderInPageModal({
        success: false,
        error: "Could not automatically locate the job description on this page. Please highlight the job text with your mouse, right-click, and select '🛡️ Scan selection with LeakedIn'."
      });
      return;
    }

    // Set loading state on button
    btnIcon.textContent = "⏳";
    btnText.textContent = "Checking...";
    floatingBtn.style.opacity = "0.85";

    chrome.runtime.sendMessage(
      { action: "scanText", text: jobText },
      (response) => {
        // Restore button state
        btnIcon.textContent = "🛡️";
        btnText.textContent = "Check this job";
        floatingBtn.style.opacity = "1";

        if (chrome.runtime.lastError) {
          renderInPageModal({
            success: false,
            error: chrome.runtime.lastError.message || "Could not communicate with the background worker."
          });
          return;
        }

        renderInPageModal(response, response?.warning);
      }
    );
  });

  // ---------------------------------------------------------------------------
  // Context Menu Response Listener
  // ---------------------------------------------------------------------------
  chrome.runtime.onMessage.addListener((msg) => {
    if (msg.action === "showScanNotification" && msg.result) {
      renderInPageModal(msg.result, msg.result.warning);
    }
  });
})();
