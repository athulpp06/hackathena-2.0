/**
 * LeakedIn Chrome Extension — Popup Controller (Manifest V3)
 *
 * Security:
 * - 100% textContent and DOM API only. Zero innerHTML.
 * - All network calls are dispatched through the background service worker.
 * - Scans execute ONLY upon explicit user click.
 * - Zero scanned text stored.
 */

const DEFAULT_API_BASE = "http://localhost:8000";
const MAX_TEXT_LENGTH = 50000;
const MIN_TEXT_LENGTH = 10;

document.addEventListener("DOMContentLoaded", async () => {
  // DOM References
  const apiInput = document.getElementById("api-base-input");
  const settingsPane = document.getElementById("settings-pane");
  const btnToggleSettings = document.getElementById("btn-settings-toggle");
  const btnSaveSettings = document.getElementById("btn-save-settings");
  const settingsStatus = document.getElementById("settings-status");

  const textarea = document.getElementById("popup-text-input");
  const charCounter = document.getElementById("char-counter");
  const btnScan = document.getElementById("btn-scan");

  const loadingEl = document.getElementById("popup-loading");
  const warningEl = document.getElementById("popup-warning");
  const errorEl = document.getElementById("popup-error");
  const errorTitle = document.getElementById("error-title");
  const errorMessage = document.getElementById("error-message");

  const gatekeeperView = document.getElementById("gatekeeper-view");
  const gatekeeperReason = document.getElementById("gatekeeper-reason");
  const gatekeeperRec = document.getElementById("gatekeeper-recommendation");

  const analysisView = document.getElementById("analysis-view");
  const scoreBadge = document.getElementById("score-badge");
  const resultLevel = document.getElementById("result-level");
  const resultVerdict = document.getElementById("result-verdict");

  const redFlagsSec = document.getElementById("red-flags-section");
  const redFlagsTitle = document.getElementById("red-flags-title");
  const redFlagsList = document.getElementById("red-flags-list");

  const domainFlagsSec = document.getElementById("domain-flags-section");
  const domainFlagsTitle = document.getElementById("domain-flags-title");
  const domainFlagsList = document.getElementById("domain-flags-list");

  const recBox = document.getElementById("recommendation-box");
  const recText = document.getElementById("recommendation-text");

  const helplineNotice = document.getElementById("helpline-notice");

  // Load configured API Base
  try {
    const storage = await chrome.storage.sync.get({ apiBase: DEFAULT_API_BASE });
    apiInput.value = storage.apiBase || DEFAULT_API_BASE;
  } catch (_) {
    apiInput.value = DEFAULT_API_BASE;
  }

  // Settings pane toggle
  btnToggleSettings.addEventListener("click", () => {
    const isOpen = settingsPane.style.display !== "none";
    settingsPane.style.display = isOpen ? "none" : "flex";
    settingsStatus.style.display = "none";
  });

  // Save Settings
  btnSaveSettings.addEventListener("click", async () => {
    let rawVal = apiInput.value.trim();
    if (!rawVal) rawVal = DEFAULT_API_BASE;

    // Remove trailing slash
    rawVal = rawVal.replace(/\/+$/, "");

    try {
      await chrome.storage.sync.set({ apiBase: rawVal });
      apiInput.value = rawVal;
      settingsStatus.textContent = "✓ Settings saved!";
      settingsStatus.style.display = "block";
      setTimeout(() => {
        settingsStatus.style.display = "none";
        settingsPane.style.display = "none";
      }, 1200);
    } catch (e) {
      settingsStatus.textContent = "Error saving settings.";
      settingsStatus.style.display = "block";
    }
  });

  // Character counter updates
  textarea.addEventListener("input", () => {
    const len = textarea.value.length;
    charCounter.textContent = `${len.toLocaleString()} chars`;
    if (len > MAX_TEXT_LENGTH) {
      charCounter.style.color = "#f59e0b";
    } else {
      charCounter.style.color = "#64748b";
    }
  });

  // Check if background worker has a recent scan cached in memory
  chrome.runtime.sendMessage({ action: "getLastResult" }, (response) => {
    if (response && response.lastScan && response.lastScan.data) {
      renderAnalysisResult(response.lastScan.data, response.lastScan.warning);
    }
  });

  // Reset UI View Helper
  function resetViews() {
    loadingEl.style.display = "none";
    warningEl.style.display = "none";
    errorEl.style.display = "none";
    gatekeeperView.style.display = "none";
    analysisView.style.display = "none";
  }

  // Display Error State
  function showError(title, message) {
    resetViews();
    errorTitle.textContent = title;
    errorMessage.textContent = message;
    errorEl.style.display = "block";
  }

  // Display Result Helper
  function renderAnalysisResult(data, warningText) {
    resetViews();

    if (warningText) {
      warningEl.textContent = `ℹ️ ${warningText}`;
      warningEl.style.display = "block";
    }

    // CASE 1: Gatekeeper Rejection (Not a job posting)
    if (data.is_job_posting === false) {
      gatekeeperReason.textContent =
        data.gatekeeper_reasoning ||
        data.verdict ||
        "The submitted text does not resemble a job vacancy or recruitment advertisement.";

      const recs = data.recommendations || [];
      if (recs.length > 0 && recs[0]) {
        gatekeeperRec.textContent = `Recommendation: ${recs[0]}`;
        gatekeeperRec.style.display = "block";
      } else {
        gatekeeperRec.style.display = "none";
      }

      gatekeeperView.style.display = "flex";
      return;
    }

    // CASE 2: Valid Job Posting Analysis
    const score = Math.max(0, Math.min(100, Math.round(Number(data.risk_score) || 0)));

    // Badge color according to backend aggregator thresholds:
    // 0-25 green, 26-50 yellow, 51-75 orange, 76-100 red
    let color = "#10b981"; // Safe (0-25)
    if (score > 75) {
      color = "#ef4444"; // High Risk (76-100)
    } else if (score > 50) {
      color = "#f97316"; // Suspicious (51-75)
    } else if (score > 25) {
      color = "#f59e0b"; // Low Risk (26-50)
    }

    scoreBadge.textContent = String(score);
    scoreBadge.style.borderColor = color;
    scoreBadge.style.color = color;

    resultLevel.textContent = data.risk_level || "Unknown";
    resultLevel.style.color = color;

    resultVerdict.textContent = data.verdict || "";

    // Clear previous lists safely
    while (redFlagsList.firstChild) {
      redFlagsList.removeChild(redFlagsList.firstChild);
    }
    while (domainFlagsList.firstChild) {
      domainFlagsList.removeChild(domainFlagsList.firstChild);
    }

    // Red Flags
    const redFlags = data.red_flags || [];
    if (redFlags.length > 0) {
      redFlagsTitle.textContent = `🚩 Red Flags (${redFlags.length}):`;
      redFlags.slice(0, 4).forEach((flag) => {
        const item = document.createElement("div");
        item.className = "flag-item";

        const titleStrong = document.createElement("strong");
        titleStrong.textContent = `[${flag.severity || "FLAG"}] ${flag.title || flag.category || "Red Flag"}: `;

        const matchSpan = document.createElement("span");
        matchSpan.textContent = flag.matched_text
          ? `"${flag.matched_text}"`
          : (flag.explanation || flag.message || "");

        item.appendChild(titleStrong);
        item.appendChild(matchSpan);
        redFlagsList.appendChild(item);
      });
      redFlagsSec.style.display = "flex";
    } else {
      redFlagsSec.style.display = "none";
    }

    // Domain Flags
    const domainFlags = data.domain_flags || [];
    if (domainFlags.length > 0) {
      domainFlagsTitle.textContent = `🌐 Domain Alerts (${domainFlags.length}):`;
      domainFlags.slice(0, 3).forEach((df) => {
        const item = document.createElement("div");
        item.className = "domain-flag-item";

        const titleStrong = document.createElement("strong");
        titleStrong.textContent = `${df.title || "Domain Alert"}: `;

        const detailSpan = document.createElement("span");
        detailSpan.textContent = df.detail || "";

        item.appendChild(titleStrong);
        item.appendChild(detailSpan);
        domainFlagsList.appendChild(item);
      });
      domainFlagsSec.style.display = "flex";
    } else {
      domainFlagsSec.style.display = "none";
    }

    // First Recommendation
    const recs = data.recommendations || [];
    if (recs.length > 0 && recs[0]) {
      recText.textContent = recs[0];
      recBox.style.display = "block";
    } else {
      recBox.style.display = "none";
    }

    // 1930 Cybercrime Helpline Notice for High Risk
    if (data.risk_level === "High Risk" || score >= 76) {
      helplineNotice.style.display = "block";
    } else {
      helplineNotice.style.display = "none";
    }

    analysisView.style.display = "flex";
  }

  // Scan Button Event Listener
  btnScan.addEventListener("click", () => {
    const raw = textarea.value;
    const trimmed = raw.trim();

    // Check empty selection
    if (!trimmed || trimmed.length === 0) {
      showError(
        "⚠️ Empty Selection",
        "Please paste or enter job posting text to scan."
      );
      return;
    }

    // Check minimum length
    if (trimmed.length < MIN_TEXT_LENGTH) {
      showError(
        "⚠️ Text Too Short",
        `Selected text has ${trimmed.length} characters. Minimum ${MIN_TEXT_LENGTH} characters required for analysis.`
      );
      return;
    }

    // Client-side text length notice
    let textToScan = trimmed;
    let localWarning = null;
    if (textToScan.length > MAX_TEXT_LENGTH) {
      textToScan = textToScan.slice(0, MAX_TEXT_LENGTH);
      localWarning = `Text was truncated to the maximum supported length of ${MAX_TEXT_LENGTH.toLocaleString()} characters.`;
    }

    resetViews();
    loadingEl.style.display = "flex";
    btnScan.disabled = true;

    // Send scan request to background service worker (NEVER direct fetch)
    chrome.runtime.sendMessage(
      { action: "scanText", text: textToScan },
      (response) => {
        btnScan.disabled = false;
        loadingEl.style.display = "none";

        if (chrome.runtime.lastError) {
          showError(
            "⚠️ Communication Error",
            chrome.runtime.lastError.message || "Failed to reach background service worker."
          );
          return;
        }

        if (!response || !response.success) {
          showError(
            "⚠️ Scan Failed",
            response?.error || "An unknown error occurred while communicating with the backend."
          );
          return;
        }

        renderAnalysisResult(
          response.data,
          response.warning || localWarning
        );
      }
    );
  });
});
