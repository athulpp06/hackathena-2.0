/**
 * LeakedIn Chrome Extension — Background Service Worker (Manifest V3)
 *
 * Responsibilities:
 * - Registers right-click context menu "Scan selection with LeakedIn"
 * - Executes all network calls with 20s timeout and detailed error classification
 * - Maintains latest scan result in memory for popup inspection (never stores raw text)
 * - Updates toolbar badge and severity colors matching backend aggregator thresholds
 */

const DEFAULT_API_BASE = "http://localhost:8000";
const MAX_TEXT_LENGTH = 50000;
const MIN_TEXT_LENGTH = 10;
const REQUEST_TIMEOUT_MS = 20000;

// In-memory cache for popup view — ZERO scanned text stored
let lastScanResult = null;

/**
 * Retrieves configured API base URL from chrome.storage.sync
 */
async function getApiBase() {
  try {
    const storage = await chrome.storage.sync.get({ apiBase: DEFAULT_API_BASE });
    const base = storage.apiBase || DEFAULT_API_BASE;
    return base.trim().replace(/\/+$/, "");
  } catch (_) {
    return DEFAULT_API_BASE;
  }
}

/**
 * Updates action badge text and background color according to score
 */
function updateActionBadge(data) {
  if (!data) {
    chrome.action.setBadgeText({ text: "" });
    return;
  }

  if (data.is_job_posting === false) {
    chrome.action.setBadgeText({ text: "NON" });
    chrome.action.setBadgeBackgroundColor({ color: "#6b7280" }); // Gray
    return;
  }

  const score = Math.max(0, Math.min(100, Math.round(Number(data.risk_score) || 0)));
  chrome.action.setBadgeText({ text: String(score) });

  let badgeColor = "#10b981"; // Safe (0 - 25)
  if (score > 75) {
    badgeColor = "#ef4444"; // High Risk (76 - 100)
  } else if (score > 50) {
    badgeColor = "#f97316"; // Suspicious (51 - 75)
  } else if (score > 25) {
    badgeColor = "#f59e0b"; // Low Risk (26 - 50)
  }

  chrome.action.setBadgeBackgroundColor({ color: badgeColor });
}

/**
 * Core scanning worker executed within background service worker
 */
async function performScan(rawText) {
  if (!rawText || typeof rawText !== "string") {
    return {
      success: false,
      error: "Empty selection. Please highlight or paste job posting text to scan."
    };
  }

  const trimmed = rawText.trim();
  if (trimmed.length === 0) {
    return {
      success: false,
      error: "Empty selection. Please highlight or paste job posting text to scan."
    };
  }

  if (trimmed.length < MIN_TEXT_LENGTH) {
    return {
      success: false,
      error: `Selected text is too short (${trimmed.length} characters). Minimum ${MIN_TEXT_LENGTH} characters required.`
    };
  }

  let textToScan = trimmed;
  let truncationWarning = null;
  if (textToScan.length > MAX_TEXT_LENGTH) {
    textToScan = textToScan.slice(0, MAX_TEXT_LENGTH);
    truncationWarning = `Text exceeded maximum limit and was truncated to ${MAX_TEXT_LENGTH.toLocaleString()} characters.`;
  }

  const apiBase = await getApiBase();
  const endpoint = `${apiBase}/api/analyze/text`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        text: textToScan,
        company_name: "",
        contact_email: ""
      }),
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      if (response.status === 429) {
        return {
          success: false,
          error: "Rate limit reached (30 requests/minute). Please wait a moment before trying again."
        };
      }
      if (response.status === 413 || response.status === 422) {
        return {
          success: false,
          error: "Invalid text payload: Must be between 10 and 50,000 characters."
        };
      }
      return {
        success: false,
        error: `Backend error (HTTP ${response.status} ${response.statusText}).`
      };
    }

    const data = await response.json();

    // Cache result in memory for popup (zero raw text stored)
    lastScanResult = {
      data: data,
      warning: truncationWarning,
      timestamp: Date.now()
    };

    updateActionBadge(data);

    return {
      success: true,
      data: data,
      warning: truncationWarning
    };

  } catch (err) {
    clearTimeout(timeoutId);

    chrome.action.setBadgeText({ text: "ERR" });
    chrome.action.setBadgeBackgroundColor({ color: "#ef4444" });

    if (err.name === "AbortError") {
      return {
        success: false,
        error: `Request timed out after ${REQUEST_TIMEOUT_MS / 1000} seconds. Is the backend server responding?`
      };
    }

    return {
      success: false,
      error: `Backend is offline or unreachable at ${apiBase}. Please ensure your LeakedIn server is running.`
    };
  }
}

// ---------------------------------------------------------------------------
// Context Menu Setup
// ---------------------------------------------------------------------------
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "leakedin-scan-selection",
    title: "🛡️ Scan selection with LeakedIn",
    contexts: ["selection"]
  });
});

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === "leakedin-scan-selection") {
    const selectedText = info.selectionText || "";

    // Show loading badge
    chrome.action.setBadgeText({ text: "..." });
    chrome.action.setBadgeBackgroundColor({ color: "#6366f1" });

    const scanResult = await performScan(selectedText);

    // Send result to active tab for floating notification
    if (tab && tab.id) {
      chrome.tabs.sendMessage(tab.id, {
        action: "showScanNotification",
        result: scanResult
      }).catch(() => {
        // Tab may not have content script injected (e.g. Chrome Web Store or internal URL)
      });
    }
  }
});

// ---------------------------------------------------------------------------
// Message Dispatcher (Content Script & Popup Communication)
// ---------------------------------------------------------------------------
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "scanText") {
    // Show loading badge
    chrome.action.setBadgeText({ text: "..." });
    chrome.action.setBadgeBackgroundColor({ color: "#6366f1" });

    performScan(request.text).then((res) => {
      sendResponse(res);
    });
    return true; // Keep channel open for async response
  }

  if (request.action === "getLastResult") {
    sendResponse({ success: true, lastScan: lastScanResult });
    return false;
  }

  if (request.action === "clearBadge") {
    chrome.action.setBadgeText({ text: "" });
    sendResponse({ success: true });
    return false;
  }
});
