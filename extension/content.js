/**
 * LeakedIn Chrome Extension — Content Script
 * Injects a 1-click "Scan with LeakedIn" floating button on job portals:
 * LinkedIn, Indeed, Naukri.
 */

(function () {
  // Prevent duplicate injections
  if (window.__leakedinInjected) return;
  window.__leakedinInjected = true;

  // Create floating Scan Button
  const btn = document.createElement("button");
  btn.id = "leakedin-floating-btn";
  btn.innerHTML = `<span style="font-size:16px;">🛡️</span> <span>Scan with LeakedIn</span>`;
  btn.style.cssText = `
    position: fixed;
    bottom: 24px;
    right: 24px;
    z-index: 999999;
    display: flex;
    align-items: center;
    gap: 8px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: #ffffff;
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 30px;
    padding: 10px 18px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 4px 20px rgba(0,0,0,0.35);
    transition: all 0.2s ease;
  `;

  btn.addEventListener("mouseenter", () => {
    btn.style.transform = "translateY(-2px) scale(1.02)";
    btn.style.boxShadow = "0 6px 24px rgba(99,102,241,0.5)";
  });
  btn.addEventListener("mouseleave", () => {
    btn.style.transform = "translateY(0) scale(1)";
    btn.style.boxShadow = "0 4px 20px rgba(0,0,0,0.35)";
  });

  // Floating Result Card
  const modal = document.createElement("div");
  modal.id = "leakedin-result-modal";
  modal.style.cssText = `
    position: fixed;
    bottom: 80px;
    right: 24px;
    z-index: 999999;
    width: 340px;
    background: #111827;
    color: #f3f4f6;
    border: 1px solid #374151;
    border-radius: 14px;
    padding: 16px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    display: none;
    flex-direction: column;
    gap: 10px;
  `;

  document.body.appendChild(btn);
  document.body.appendChild(modal);

  // Extract visible job text from page
  function extractJobContent() {
    // Selectors for major job portals
    const selectors = [
      ".job-view-layout", // LinkedIn
      "#jobDescriptionText", // Indeed
      ".job-desc", // Naukri
      ".styles_job-desc-container__txpYf", // Naukri modern
      ".description__text", // General
      "article",
      "main"
    ];

    for (const sel of selectors) {
      const el = document.querySelector(sel);
      if (el && el.innerText.trim().length > 100) {
        return el.innerText.trim();
      }
    }

    // Fallback: selected text or top paragraphs
    const selection = window.getSelection().toString().trim();
    if (selection) return selection;

    return document.body.innerText.slice(0, 3000);
  }

  btn.addEventListener("click", () => {
    const text = extractJobContent();
    if (!text || text.length < 20) {
      alert("LeakedIn: Could not extract job posting text. Please highlight the job description and right-click to scan.");
      return;
    }

    btn.innerHTML = `<span>⏳</span> <span>Scanning...</span>`;
    btn.style.opacity = "0.8";

    chrome.runtime.sendMessage(
      { action: "scanJobText", text: text },
      (res) => {
        btn.innerHTML = `<span style="font-size:16px;">🛡️</span> <span>Scan with LeakedIn</span>`;
        btn.style.opacity = "1";

        if (res && res.success) {
          showFloatingResult(res.data);
        } else {
          showFloatingResult(null, res?.error || "Failed to contact LeakedIn API. Is http://localhost:8000 running?");
        }
      }
    );
  });

  function showFloatingResult(data, error) {
    if (error) {
      modal.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <strong style="color:#ef4444;">⚠️ Connection Error</strong>
          <button id="leakedin-close" style="background:none; border:none; color:#9ca3af; cursor:pointer; font-size:16px;">✕</button>
        </div>
        <p style="font-size:12px; color:#d1d5db; margin:6px 0 0;">${error}</p>
      `;
    } else {
      const score = data.risk_score;
      let scoreColor = "#10b981";
      if (score > 75) scoreColor = "#ef4444";
      else if (score > 50) scoreColor = "#f97316";
      else if (score > 25) scoreColor = "#f59e0b";

      const flags = data.rule_matches || data.red_flags || [];

      modal.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div style="display:flex; align-items:center; gap:6px;">
            <span style="font-size:18px;">🛡️</span>
            <strong style="font-size:15px; color:#ffffff;">LeakedIn Verdict</strong>
          </div>
          <button id="leakedin-close" style="background:none; border:none; color:#9ca3af; cursor:pointer; font-size:16px;">✕</button>
        </div>

        <div style="display:flex; align-items:center; gap:12px; margin:8px 0; background:rgba(255,255,255,0.04); padding:10px; border-radius:8px;">
          <div style="width:48px; height:48px; border-radius:50%; border:3px solid ${scoreColor}; display:flex; align-items:center; justify-content:center; font-weight:800; font-size:18px; color:${scoreColor}; flex-shrink:0;">
            ${score}
          </div>
          <div>
            <div style="font-weight:700; font-size:14px; color:${scoreColor};">${data.risk_level}</div>
            <div style="font-size:11px; color:#9ca3af; line-height:1.3; margin-top:2px;">${data.verdict}</div>
          </div>
        </div>

        ${flags.length > 0 ? `
          <div style="font-size:12px; color:#fca5a5; font-weight:600; margin-bottom:4px;">🚩 Red Flags (${flags.length}):</div>
          <div style="max-height:100px; overflow-y:auto; display:flex; flex-direction:column; gap:4px; margin-bottom:8px;">
            ${flags.slice(0, 3).map(f => `
              <div style="font-size:11px; background:rgba(239,68,68,0.12); padding:4px 8px; border-radius:4px; color:#fca5a5;">
                • <strong>${f.category}:</strong> ${f.matched_text || f.message || f.description || ''}
              </div>
            `).join('')}
          </div>
        ` : `
          <div style="font-size:12px; color:#10b981; margin-bottom:8px;">✅ No critical scam triggers found.</div>
        `}

        <a href="http://localhost:5500" target="_blank" style="display:block; text-align:center; background:#6366f1; color:#fff; text-decoration:none; font-size:12px; font-weight:600; padding:6px 10px; border-radius:6px;">
          Open Full Intelligence Report ↗
        </a>
      `;
    }

    modal.style.display = "flex";
    document.getElementById("leakedin-close").onclick = () => {
      modal.style.display = "none";
    };
  }

  // Listen for context menu triggers from background worker
  chrome.runtime.onMessage.addListener((msg) => {
    if (msg.action === "showScanNotification" && msg.data) {
      showFloatingResult(msg.data);
    }
  });
})();
