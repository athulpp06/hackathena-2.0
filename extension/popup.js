/**
 * LeakedIn Chrome Extension — Popup Controller
 */

const DEFAULT_API_BASE = "http://localhost:8000";

document.addEventListener("DOMContentLoaded", async () => {
  const apiInput = document.getElementById("api-base-input");
  const settingsPane = document.getElementById("settings-pane");
  const btnToggleSettings = document.getElementById("btn-settings-toggle");
  const btnSaveSettings = document.getElementById("btn-save-settings");
  const btnScan = document.getElementById("btn-quick-scan");
  const textarea = document.getElementById("popup-text-input");

  // Load configured API base
  const storage = await chrome.storage.sync.get({ apiBase: DEFAULT_API_BASE });
  apiInput.value = storage.apiBase || DEFAULT_API_BASE;

  // Toggle settings
  btnToggleSettings.addEventListener("click", () => {
    settingsPane.style.display = settingsPane.style.display === "none" ? "flex" : "none";
  });

  // Save settings
  btnSaveSettings.addEventListener("click", async () => {
    const val = apiInput.value.trim() || DEFAULT_API_BASE;
    await chrome.storage.sync.set({ apiBase: val });
    settingsPane.style.display = "none";
  });

  // Check if there was a recent scan from the context menu
  const localData = await chrome.storage.local.get("latestScan");
  if (localData?.latestScan?.result) {
    renderPopupResult(localData.latestScan.result);
  }

  // Scan button
  btnScan.addEventListener("click", async () => {
    const text = textarea.value.trim();
    if (!text) return;

    showLoading(true);

    try {
      const apiBase = apiInput.value.trim() || DEFAULT_API_BASE;
      const res = await fetch(`${apiBase}/api/analyze/text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, company_name: "", contact_email: "" })
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      renderPopupResult(data);
    } catch (err) {
      alert("Scan failed: " + err.message + "\nCheck if the backend is running at " + apiInput.value);
    } finally {
      showLoading(false);
    }
  });
});

function showLoading(show) {
  document.getElementById("popup-loading").style.display = show ? "flex" : "none";
  document.getElementById("popup-result").style.display = "none";
}

function renderPopupResult(data) {
  const resultCard = document.getElementById("popup-result");
  const scoreBadge = document.getElementById("score-badge");
  const levelEl = document.getElementById("result-level");
  const verdictEl = document.getElementById("result-verdict");
  const flagsList = document.getElementById("popup-flags");

  const score = data.risk_score;
  scoreBadge.textContent = score;

  let color = "#10b981";
  if (score > 75) color = "#ef4444";
  else if (score > 50) color = "#f97316";
  else if (score > 25) color = "#f59e0b";

  scoreBadge.style.borderColor = color;
  scoreBadge.style.color = color;
  levelEl.textContent = data.risk_level;
  levelEl.style.color = color;
  verdictEl.textContent = data.verdict;

  flagsList.innerHTML = "";
  const flags = data.rule_matches || data.red_flags || [];

  if (flags.length > 0) {
    flags.slice(0, 4).forEach(f => {
      const item = document.createElement("div");
      item.className = "popup-flag-item";
      item.innerHTML = `<strong>${f.category}:</strong> ${f.matched_text || f.message || f.description || ''}`;
      flagsList.appendChild(item);
    });
  } else {
    flagsList.innerHTML = `<span style="font-size:11px; color:#10b981;">✅ No severe scam patterns detected.</span>`;
  }

  resultCard.style.display = "flex";
}
