/**
 * LeakedIn Chrome Extension — Background Service Worker
 * Handles context menu actions, badge updates, and communication with LeakedIn API.
 */

const DEFAULT_API_BASE = "http://localhost:8000";

// Register Context Menu on Installation
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "leakedin-scan-selection",
    title: "🛡️ Scan selection with LeakedIn",
    contexts: ["selection"]
  });
});

// Context Menu Click Listener
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === "leakedin-scan-selection" && info.selectionText) {
    const selectedText = info.selectionText.trim();
    if (!selectedText) return;

    // Show loading badge
    chrome.action.setBadgeText({ text: "..." });
    chrome.action.setBadgeBackgroundColor({ color: "#6366f1" });

    try {
      // Get API Base URL from storage
      const storage = await chrome.storage.sync.get({ apiBase: DEFAULT_API_BASE });
      const apiBase = storage.apiBase || DEFAULT_API_BASE;

      const response = await fetch(`${apiBase}/api/analyze/text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: selectedText,
          company_name: "",
          contact_email: ""
        })
      });

      if (!response.ok) {
        throw new Error(`API returned HTTP ${response.status}`);
      }

      const data = await response.json();

      // Update badge with score
      const score = data.risk_score;
      chrome.action.setBadgeText({ text: score.toString() });

      let badgeColor = "#10b981"; // Safe
      if (score > 75) badgeColor = "#ef4444"; // High
      else if (score > 50) badgeColor = "#f97316"; // Suspicious
      else if (score > 25) badgeColor = "#f59e0b"; // Low

      chrome.action.setBadgeBackgroundColor({ color: badgeColor });

      // Save scan result to local storage for popup inspection
      await chrome.storage.local.set({
        latestScan: {
          text: selectedText,
          result: data,
          timestamp: Date.now()
        }
      });

      // Send message to content script if active
      if (tab?.id) {
        chrome.tabs.sendMessage(tab.id, {
          action: "showScanNotification",
          data: data
        }).catch(() => {});
      }

    } catch (err) {
      console.error("LeakedIn Scan Error:", err);
      chrome.action.setBadgeText({ text: "ERR" });
      chrome.action.setBadgeBackgroundColor({ color: "#6b7280" });
    }
  }
});

// Message listener for content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "scanJobText") {
    (async () => {
      try {
        const storage = await chrome.storage.sync.get({ apiBase: DEFAULT_API_BASE });
        const apiBase = storage.apiBase || DEFAULT_API_BASE;

        const response = await fetch(`${apiBase}/api/analyze/text`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            text: request.text,
            company_name: request.companyName || "",
            contact_email: request.contactEmail || ""
          })
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        sendResponse({ success: true, data });
      } catch (err) {
        sendResponse({ success: false, error: err.message });
      }
    })();
    return true; // Keep message channel open for async response
  }
});
