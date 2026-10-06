# 🛡️ LeakedIn Chrome Extension (Manifest V3)

> Instant recruitment scam and phishing detector directly inside Google Chrome, Brave, and Edge.

---

## 🚀 Features
- **1-Click Floating Button**: Injects a sleek "🛡️ Scan with LeakedIn" button when viewing job postings on **LinkedIn**, **Indeed**, and **Naukri**.
- **Context Menu Scanning**: Highlight any suspicious text or message on any website, right-click, and select **"🛡️ Scan selection with LeakedIn"**.
- **Live Risk Badge**: Shows the calculated 0–100 threat score directly in the Chrome toolbar icon with severity color coding (🟢 Safe, 🟡 Low, 🟠 Suspicious, 🔴 High Risk).
- **Zero Cloud Leakage**: Calls your local LeakedIn backend (`http://localhost:8000`) by default. No data is stored or logged.

---

## 📥 How to Install (Developer Mode)

1. Open your Chromium-based browser (Google Chrome, Brave, Microsoft Edge).
2. Navigate to `chrome://extensions/` in your address bar.
3. Toggle on **"Developer mode"** in the top-right corner.
4. Click the **"Load unpacked"** button in the top-left.
5. Select the `extension/` folder located inside this project repository:
   ```text
   c:\Users\athma\OneDrive\Desktop\GECT\hackathenna 2.0\extension
   ```
6. The **LeakedIn — AI Job Scam Detector** extension icon will now appear in your browser toolbar!

---

## ⚙️ Configuration
By default, the extension connects to the local FastAPI backend at `http://localhost:8000`.
To connect to a custom or hosted deployment:
1. Click the LeakedIn toolbar icon to open the popup.
2. Click the gear icon (**⚙️**).
3. Update the **API Base URL** (e.g. `https://your-leakedin-api.onrender.com`).
4. Click **Save**.

---

## 🔒 Permissions Policy
- `contextMenus`: Used only to create the "Scan selection with LeakedIn" right-click action.
- `storage`: Used solely to store your preferred API base URL and latest scan summary locally in your browser.
- `activeTab`: Used to capture selected text only when explicitly triggered by the user.
- **No analytics, no ad tracking, and no external tracking scripts.**
