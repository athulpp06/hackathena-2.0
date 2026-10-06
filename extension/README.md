<p align="center">
  <img src="../frontend/assets/brand/logo.svg" alt="LeakedIn" width="240" />
</p>

# LeakedIn Chrome Extension (Manifest V3)

> Instant recruitment scam and phishing detector directly inside Google Chrome, Brave, and Edge.

---

## 🚀 Features
- **1-Click Floating Button**: Injects a sleek "🛡️ Check this job" button when viewing job postings on **LinkedIn**, **Indeed**, and **Naukri**.
- **Context Menu Scanning**: Highlight any job text or message on any website, right-click, and select **"🛡️ Scan selection with LeakedIn"**.
- **Quick Popup Scanner**: Paste any job description directly into the extension popup for instant analysis.
- **Live Risk Badge**: Shows the calculated 0–100 threat score directly in the Chrome toolbar icon with severity color coding (🟢 Safe 0-25, 🟡 Low 26-50, 🟠 Suspicious 51-75, 🔴 High Risk 76-100).
- **Gatekeeper Awareness**: Flags non-job postings gracefully ("This doesn't look like a job posting").
- **1930 Helpline Alert**: Direct emergency guidance for high-risk fraud cases.
- **Zero Cloud Leakage**: Calls your configured LeakedIn backend (`http://localhost:8000` by default). No text stored.

---

## 📥 How to Install (Developer Mode)

1. Open your Chromium-based browser (Google Chrome, Brave, Microsoft Edge).
2. Navigate to `chrome://extensions/` in your address bar.
3. Toggle on **"Developer mode"** in the top-right corner.
4. Click the **"Load unpacked"** button in the top-left.
5. Select the `extension/` folder located inside this repository.
6. The **LeakedIn — AI Job Scam Detector** extension icon will appear in your browser toolbar (pin it for quick access)!

---

## ⚙️ Configuration
By default, the extension connects to the local FastAPI backend at `http://localhost:8000`.
To connect to a custom or hosted deployment:
1. Click the LeakedIn toolbar icon to open the popup.
2. Click the gear icon (**⚙️**).
3. Update the **API Base URL** (e.g. `http://localhost:8000` or `https://your-leakedin-api.example.com`).
4. Click **Save**.

---

## 🔒 Permissions Policy
- `contextMenus`: Used only to create the "Scan selection with LeakedIn" right-click action.
- `storage`: Used solely to store your preferred API base URL setting (`chrome.storage.sync`).
- `activeTab`: Used to display the scan results modal only when explicitly triggered by the user.
- `host_permissions`: Configured only for the backend API origin (`http://localhost:8000/*`, `http://127.0.0.1:8000/*`) and the three supported job portals (LinkedIn, Indeed, Naukri).
- **Zero remote code, zero eval, zero analytics, zero ad tracking.**
