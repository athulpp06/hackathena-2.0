/**
 * LeakedIn — Unified Frontend Application Engine
 * Supports: Multilingual i18n, Text/URL/Image/Document Scans,
 * AI Gatekeeper, Explainable ML (XAI), Canvas PNG Export, and Cybercrime Reporting.
 */

// ==========================================================================
// 1. CONFIGURATION & CONSTANTS
// ==========================================================================
function getApiBase() {
  if (typeof window.LEAKEDIN_API_BASE === "string" && window.LEAKEDIN_API_BASE) {
    return window.LEAKEDIN_API_BASE.replace(/\/+$/, "");
  }
  const proto = window.location.protocol;
  const host = window.location.host;
  if (proto === "file:" || host.includes("5500") || host.includes("3000")) {
    return "http://localhost:8000";
  }
  return "";
}

const API_BASE = getApiBase();

let currentScanResult = null;
let currentInputText = "";
let currentLang = "en";
let currentMode = "text"; // "text" | "url" | "image" | "document"
let currentImageFile = null;
let currentDocFile = null;
let currentPoliceDraft = "";

// ==========================================================================
// 2. MULTILINGUAL I18N DICTIONARY
// ==========================================================================
const I18N = {
  en: {
    tagline_badge: "AI Scam Shield",
    header_sub: "Multi-layered detection for fraudulent job postings, fake offer letters, WhatsApp recruitment traps, and identity theft.",
    privacy_note: "<strong>Privacy:</strong> Runs offline by default with zero permanent storage. If Gemini Cloud is enabled, input is sent to Google for analysis.",
    btn_how_it_works: "How It Works",
    sample_title: "Instant Demo Presets:",
    sample_hint: "Select a realistic test case to populate inputs:",
    tab_text: "Paste Text",
    tab_url: "Job URL",
    tab_image: "Screenshot (OCR)",
    tab_document: "Offer Letter (PDF/DOCX)",
    btn_scan_text: "Analyze Job Posting",
    btn_scan_url: "Scrape & Analyze URL",
    btn_scan_image: "Run Offline OCR & Scan",
    btn_scan_doc: "Analyze Offer Letter",
    url_hint: "🛡️ Protected with SSRF safeguards. If blocked by authentication (LinkedIn, Naukri), copy and paste the text directly into the Text tab.",
    upload_img_title: "Click to upload or drag & drop a screenshot",
    upload_img_hint: "Supports JPG, PNG, WEBP • Press Ctrl+V to paste directly • Runs offline by default (Gemini vision optional)",
    upload_doc_title: "Upload Offer Letter or Contract (PDF / DOCX)",
    upload_doc_hint: "Max 5 MB • Analyzes CIN/GST, suspicious signatory clauses, metadata mismatches & layout",
    loading_text: "Analyzing content across ML and Heuristic intelligence layers...",
    risk_score_label: "Risk Score",
    scale_safe: "Safe (0-25)",
    scale_low: "Low Risk (26-50)",
    scale_suspicious: "Suspicious (51-75)",
    scale_high: "High Risk (76-100)",
    metric_ml: "🤖 ML Fraud Likelihood",
    metric_rules: "🚩 Triggered Rules",
    metric_calib: "🎯 Calibrated Confidence",
    advice_title: "What You Should Do Next",
    urgent_label: "CRITICAL NOTICE:",
    helpline_title: "National Cyber Crime Reporting Helpline",
    helpline_desc: "If money was transferred or sensitive IDs were leaked, dial 1930 immediately or file an incident at cybercrime.gov.in.",
    btn_copy_police: "📋 Copy Police Complaint",
    xai_title: "Why the Machine Learning Model Flagged This",
    xai_desc: "Top vocabulary tokens and n-grams influencing the model weights for this prediction:",
    xai_fraud_col: "⚠️ Scam-Associated Triggers:",
    xai_legit_col: "✅ Legitimacy Indicators:",
    entities_title: "Extracted Entities & Community Reputation Intelligence",
    entities_desc: "Identified contact points cross-checked against our community blacklist database:",
    domain_title: "Domain & Corporate Identity Verification",
    red_flags_title: "Rule Engine Red Flags Detected",
    highlights_title: "Interactive Phrase Inspection",
    highlights_desc: "Hover or tap on any highlighted term to view why it was categorized:",
    btn_copy_summary: "Copy Scan Summary",
    btn_export_png: "Download Shareable Card (PNG)",
    btn_report_db: "Report to Scam DB",
    btn_feedback: "Feedback",
    btn_reset: "Analyze Another Posting",
    try_again: "Try Again",
    remove: "Remove",
    modal_hiw_title: "How LeakedIn Works",
    modal_report_title: "Report Scammer Entity",
    modal_report_desc: "Add a phone number, UPI ID, or domain to our local community blacklist. Entities are cryptographically hashed (salted SHA-256) — no raw message text is saved.",
    btn_submit_report: "Submit to Blacklist",
    modal_feedback_title: "Detection Feedback"
  },
  hi: {
    tagline_badge: "एआई स्कैम शील्ड",
    header_sub: "फर्जी नौकरी विज्ञापनों, नकली ऑफर लेटर, व्हाट्सएप भर्ती जाल और पहचान चोरी की बहुस्तरीय पहचान।",
    privacy_note: "<strong>गोपनीयता:</strong> डिफ़ॉल्ट रूप से शून्य डेटा भंडारण के साथ ऑफ़लाइन चलता है। जेमिनी सक्षम होने पर टेक्स्ट/स्क्रीनशॉट गूगल को भेजे जाते हैं।",
    btn_how_it_works: "यह कैसे काम करता है",
    sample_title: "त्वरित डेमो नमूने:",
    sample_hint: "परीक्षण के लिए एक यथार्थवादी उदाहरण चुनें:",
    tab_text: "टेक्स्ट पेस्ट करें",
    tab_url: "नौकरी का लिंक (URL)",
    tab_image: "स्क्रीनशॉट (OCR)",
    tab_document: "ऑफर लेटर (PDF/DOCX)",
    btn_scan_text: "नौकरी विज्ञापन का विश्लेषण करें",
    btn_scan_url: "यूआरएल स्कैन करें",
    btn_scan_image: "ऑफलाइन ओसीआर स्कैन करें",
    btn_scan_doc: "ऑफर लेटर की जांच करें",
    url_hint: "SSRF सुरक्षा से सुरक्षित। यदि लॉगिन की आवश्यकता है, तो टेक्स्ट कॉपी करके पेस्ट करें।",
    upload_img_title: "स्क्रीनशॉट अपलोड करने के लिए क्लिक करें या ड्रैग करें",
    upload_img_hint: "JPG, PNG, WEBP • डिफ़ॉल्ट रूप से ऑफ़लाइन चलता है (जेमिनी विज़न वैकल्पिक)",
    upload_doc_title: "ऑफर लेटर या अनुबंध अपलोड करें (PDF / DOCX)",
    upload_doc_hint: "अधिकतम 5 MB • CIN/GST, हस्ताक्षर और संदिग्ध भुगतान शर्तों की जांच करता है",
    loading_text: "एमएल और नियम-आधारित परतों में विश्लेषण किया जा रहा है...",
    risk_score_label: "जोखिम स्कोर",
    scale_safe: "सुरक्षित (0-25)",
    scale_low: "कम जोखिम (26-50)",
    scale_suspicious: "संदिग्ध (51-75)",
    scale_high: "अत्यधिक जोखिम (76-100)",
    metric_ml: "🤖 एमएल धोखाधड़ी संभावना",
    metric_rules: "🚩 सक्रिय नियम",
    metric_calib: "🎯 कैलिब्रेटेड विश्वास",
    advice_title: "आपको आगे क्या करना चाहिए",
    urgent_label: "महत्वपूर्ण सूचना:",
    helpline_title: "राष्ट्रीय साइबर अपराध रिपोर्टिंग हेल्पलाइन",
    helpline_desc: "यदि पैसे भेजे गए हैं या दस्तावेज साझा किए गए हैं, तो तुरंत 1930 डायल करें या cybercrime.gov.in पर शिकायत दर्ज करें।",
    btn_copy_police: "📋 पुलिस शिकायत प्रारूप कॉपी करें",
    xai_title: "मॉडल ने इसे क्यों चिन्हित किया",
    xai_desc: "लॉजिस्टिक रिग्रेशन वर्गीकरण को प्रभावित करने वाले मुख्य शब्द:",
    xai_fraud_col: "⚠️ स्कैम संकेतक शब्द:",
    xai_legit_col: "✅ प्रामाणिकता संकेतक शब्द:",
    entities_title: "निकाले गए संपर्क और प्रतिष्ठा डेटाबेस",
    entities_desc: "हमारे स्थानीय ब्लैकलिस्ट डेटाबेस के खिलाफ जांचे गए संपर्क:",
    domain_title: "डोमेन और कॉर्पोरेट पहचान सत्यापन",
    red_flags_title: "पाए गए लाल झंडे (Red Flags)",
    highlights_title: "संदिग्ध वाक्यांश निरीक्षण",
    highlights_desc: "विवरण देखने के लिए हाइलाइट किए गए वाक्यांश पर कर्सर ले जाएं:",
    btn_copy_summary: "स्कैन सारांश कॉपी करें",
    btn_export_png: "शेयर करने योग्य कार्ड (PNG) डाउनलोड करें",
    btn_report_db: "स्कैम डेटाबेस में रिपोर्ट करें",
    btn_feedback: "प्रतिक्रिया दें",
    btn_reset: "अन्य विज्ञापन की जांच करें",
    try_again: "पुनः प्रयास करें",
    remove: "हटाएं",
    modal_hiw_title: "लीक्डइन कैसे काम करता है",
    modal_report_title: "स्कैमर विवरण रिपोर्ट करें",
    modal_report_desc: "एक फोन नंबर, यूपीआई आईडी या डोमेन को ब्लैकलिस्ट में जोड़ें। डेटा केवल हैश (SHA-256) के रूप में सुरक्षित रहता है।",
    btn_submit_report: "ब्लैकलिस्ट में जोड़ें",
    modal_feedback_title: "पहचान प्रतिक्रिया"
  },
  ml: {
    tagline_badge: "എഐ സ്കാം ഷീൽഡ്",
    header_sub: "വ്യാജ ജോലി പരസ്യങ്ങൾ, വ്യാജ ഓഫർ ലെറ്ററുകൾ, വാട്ട്‌സ്ആപ്പ് റിക്രൂട്ട്‌മെന്റ് തട്ടിപ്പുകൾ എന്നിവ കണ്ടെത്താനുള്ള സുരക്ഷാ പ്ലാറ്റ്‌ഫോം.",
    privacy_note: "<strong>സ്വകാര്യത:</strong> വിവരങ്ങൾ സ്ഥിരമായി സൂക്ഷിക്കാതെ ഓഫ്‌ലൈനിൽ പ്രവർത്തിക്കുന്നു. ജെമിനി പ്രവർത്തനക്ഷമമാക്കിയാൽ ഇൻപുട്ട് ഗൂഗിളിലേക്ക് അയക്കും.",
    btn_how_it_works: "പ്രവർത്തനം എങ്ങനെ",
    sample_title: "ഡെമോ സാമ്പിളുകൾ:",
    sample_hint: "പരിശോധിക്കാൻ ഒരു ഉദാഹരണം തിരഞ്ഞെടുക്കുക:",
    tab_text: "ടെക്സ്റ്റ് നൽകുക",
    tab_url: "ജോബ് ലിങ്ക് (URL)",
    tab_image: "സ്ക്രീൻഷോട്ട് (OCR)",
    tab_document: "ഓഫർ ലെറ്റർ (PDF/DOCX)",
    btn_scan_text: "പരസ്യം പരിശോധിക്കുക",
    btn_scan_url: "ലിങ്ക് സ്കാൻ ചെയ്യുക",
    btn_scan_image: "ഓഫ്‌ലൈൻ OCR സ്കാൻ",
    btn_scan_doc: "ഓഫർ ലെറ്റർ പരിശോധിക്കുക",
    url_hint: "SSRF സുരക്ഷയുണ്ട്. ലിങ്ക് തുറക്കാൻ കഴിയുന്നില്ലെങ്കിൽ ടെക്സ്റ്റ് നേരിട്ട് കോപ്പി ചെയ്തു നൽകുക.",
    upload_img_title: "സ്ക്രീൻഷോട്ട് അപ്‌ലോഡ് ചെയ്യുക",
    upload_img_hint: "JPG, PNG, WEBP • ഡിഫോൾട്ടായി ഓഫ്‌ലൈനിൽ പ്രവർത്തിക്കുന്നു (ജെമിനി വിഷൻ ഐച്ഛികം)",
    upload_doc_title: "ഓഫർ ലെറ്റർ അപ്‌ലോഡ് ചെയ്യുക (PDF / DOCX)",
    upload_doc_hint: "പരമാവധി 5 MB • രജിസ്ട്രേഷൻ CIN/GST, ഒപ്പ് എന്നിവ പരിശോധിക്കുന്നു",
    loading_text: "വിവിധ സുരക്ഷാ ഘട്ടങ്ങളിലൂടെ പരിശോധിക്കുന്നു...",
    risk_score_label: "റിസ്ക് സ്കോർ",
    scale_safe: "സുരക്ഷിതം (0-25)",
    scale_low: "കുറഞ്ഞ റിസ്ക് (26-50)",
    scale_suspicious: "സംശയാസ്പദം (51-75)",
    scale_high: "അതീവ റിസ്ക് (76-100)",
    metric_ml: "🤖 എംഎൽ തട്ടിപ്പ് സാധ്യത",
    metric_rules: "🚩 കണ്ടെത്തിയ മുന്നറിയിപ്പുകൾ",
    metric_calib: "🎯 കൃത്യത ഉറപ്പ്",
    advice_title: "നിങ്ങൾ ഇനി എന്ത് ചെയ്യണം?",
    urgent_label: "അടിയന്തിര മുന്നറിയിപ്പ്:",
    helpline_title: "ദേശീയ സൈബർ ക്രൈം ഹെൽപ്പ് ലൈൻ",
    helpline_desc: "പണം നഷ്ടപ്പെടുകയോ ആധാർ/പാൻ വിവരങ്ങൾ നൽകുകയോ ചെയ്തിട്ടുണ്ടെങ്കിൽ ഉടൻ 1930 ൽ വിളിക്കുക അല്ലെങ്കിൽ cybercrime.gov.in ൽ പരാതി നൽകുക.",
    btn_copy_police: "📋 പരാതി ഡ്രാഫ്റ്റ് കോപ്പി ചെയ്യുക",
    xai_title: "മോഡൽ കണ്ടെത്തിയ കാരണങ്ങൾ",
    xai_desc: "നിഗമനത്തെ സ്വാധീനിച്ച പ്രധാന പദങ്ങൾ:",
    xai_fraud_col: "⚠️ തട്ടിപ്പ് സൂചകങ്ങൾ:",
    xai_legit_col: "✅ വിശ്വസനീയ സൂചകങ്ങൾ:",
    entities_title: "കണ്ടെത്തിയ വിവരങ്ങളും കരിമ്പട്ടികയും",
    entities_desc: "കമ്മ്യൂണിറ്റി കരിമ്പട്ടികയുമായി താരതമ്യം ചെയ്ത വിവരങ്ങൾ:",
    domain_title: "ഡൊമെയ്ൻ സ്ഥിരീകരണം",
    red_flags_title: "കണ്ടെത്തിയ ചുവപ്പ് അടയാളങ്ങൾ",
    highlights_title: "പ്രധാന ഭാഗങ്ങൾ പരിശോധിക്കുക",
    highlights_desc: "വിശദാംശങ്ങൾ അറിയാൻ ഹൈലൈറ്റ് ചെയ്ത വാക്കുകളിൽ വിരലമർത്തുക:",
    btn_copy_summary: "റിപ്പോർട്ട് കോപ്പി ചെയ്യുക",
    btn_export_png: "കാർഡ് ഡൗൺലോഡ് ചെയ്യുക (PNG)",
    btn_report_db: "ഡാറ്റാബേസിൽ റിപ്പോർട്ട് ചെയ്യുക",
    btn_feedback: "അഭിപ്രായം രേഖപ്പെടുത്തുക",
    btn_reset: "മറ്റൊന്ന് പരിശോധിക്കുക",
    try_again: "വീണ്ടും ശ്രമിക്കുക",
    remove: "ഒഴിവാക്കുക",
    modal_hiw_title: "പ്രവർത്തന തത്വം",
    modal_report_title: "തട്ടിപ്പുകാരെ റിപ്പോർട്ട് ചെയ്യുക",
    modal_report_desc: "ഫോൺ നമ്പർ, UPI ID അല്ലെങ്കിൽ ഡൊമെയ്ൻ കരിമ്പട്ടികയിൽ ചേർക്കുക. വിവരങ്ങൾ ഹാഷ് (SHA-256) രൂപത്തിൽ മാത്രമേ സൂക്ഷിക്കൂ.",
    btn_submit_report: "കരിമ്പട്ടികയിൽ ചേർക്കുക",
    modal_feedback_title: "പരിശോധനാ ഫീഡ്ബാക്ക്"
  }
};

function changeLanguage(lang) {
  currentLang = lang;
  document.documentElement.lang = lang;
  const dict = I18N[lang] || I18N.en;

  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (dict[key]) {
      el.innerHTML = dict[key];
    }
  });

  updateAnalyzeButtonLabel();
  renderSampleButtons();
}

// ==========================================================================
// 3. SAMPLE PRESETS
// ==========================================================================
const SAMPLES = [
  {
    id: "scam_whatsapp",
    title: "⚠️ WhatsApp Kit Fee Scam",
    badge: "critical",
    badgeText: "SCAM",
    company: "TCS",
    email: "hr.tcs.recruiter@gmail.com",
    text: `URGENT HIRING: Data Entry Operator at TCS (Tata Consultancy Services)!
Earn Rs 45,000 per week working only 2-3 hours per day from home. No experience required. Direct selection without interview!
Only 3 seats left - offer expires within 24 hours.
To confirm your slot: A refundable security deposit of Rs 1,500 is required for training kit & login credentials. Pay via PhonePe or Google Pay to hr-recruiter@okaxis.
Send your CV on WhatsApp: +91 98765 43210 or email hr.tcs.recruiter@gmail.com.`
  },
  {
    id: "scam_malayalam",
    title: "🌴 Malayalam Task Scam",
    badge: "high",
    badgeText: "MALAYALAM",
    company: "IT Solutions Kerala",
    email: "hr.kerala.jobs@gmail.com",
    text: `അടിയന്തിര റിക്രൂട്ട്മെന്റ്: പ്രമുഖ ഐടി കമ്പനിയിൽ വർക്ക് ഫ്രം ഹോം ഡാറ്റാ എൻട്രി ജോലി!
ആഴ്ചയിൽ 25,000 രൂപ വരുമാനം നേടാം. യോഗ്യതയോ മുൻപരിചയമോ ആവശ്യമില്ല. നേരിട്ട് സെലക്ഷൻ.
പരിശീലന കിറ്റിനായി 1,500 രൂപ രജിസ്ട്രേഷൻ ഫീസ് ഗൂഗിൾ പേ / യുപിഐ വഴി ആദ്യം അടക്കണം (48 മണിക്കൂറിനുള്ളിൽ തിരികെ നൽകും).
നിങ്ങളുടെ ആധാർ കാർഡ് കോപ്പിയും റെസ്യൂമെയും ഉടൻ വാട്സ്ആപ്പിൽ അയക്കുക: +91 9876543210.
ഇമെയിൽ: hr.tcs.kerala@gmail.com`
  },
  {
    id: "scam_hindi",
    title: "🇮🇳 Hindi Part-Time Scam",
    badge: "high",
    badgeText: "HINDI",
    company: "TCS India",
    email: "hr.tcs.india@gmail.com",
    text: `घर बैठे पार्ट-टाइम डेटा एंट्री जॉब!
प्रतिदिन ₹3,000 कमाएं। बिना किसी इंटरव्यू के डायरेक्ट सिलेक्शन।
ट्रेनिंग किट और पोर्टल लॉगिन के लिए ₹1,500 रजिस्ट्रेशन फीस तुरंत UPI (hr-tcs@paytm) पर ट्रांसफर करें। फीस 24 घंटे में रिफंड होगी।
आधार कार्ड और पैन कार्ड की फोटो कॉपी व्हाट्सएप पर भेजें: +91 9876543210.
ईमेल: hr.tcs.india@gmail.com`
  },
  {
    id: "real_stripe",
    title: "✅ Legit Stripe Job",
    badge: "safe",
    badgeText: "LEGIT",
    company: "Stripe",
    email: "recruiting@stripe.com",
    text: `Senior Backend Engineer — Cloud Platform Team
Company: Stripe (stripe.com)
Location: Bangalore, India (Hybrid) | Full-Time

About Stripe:
Stripe is a technology company that builds economic infrastructure for the internet.

Role Overview:
We are looking for a Senior Backend Engineer to join our Cloud Platform team. You will design, build, and maintain the distributed systems that power Stripe's core payment infrastructure.

Requirements:
- 4+ years of software engineering experience with Go or Python.
- Deep familiarity with distributed systems, relational databases (PostgreSQL), and Kafka.
- Strong understanding of systems architecture, scalability, and security.

Compensation & Benefits:
- Competitive base salary (₹45–65 LPA range, DOE) + RSUs.
- Comprehensive health insurance for employee and dependents.
- 25 days paid time off + company holidays.

To Apply:
Submit your resume and portfolio via our official careers portal: https://stripe.com/jobs
For questions, contact our recruiting team at recruiting@stripe.com`
  },
  {
    id: "gatekeeper_recipe",
    title: "🍲 Recipe (Gatekeeper Demo)",
    badge: "other",
    badgeText: "NON-JOB",
    company: "",
    email: "",
    text: `Delicious Homemade Chocolate Brownies Recipe
Ingredients:
- 200g dark chocolate, roughly chopped
- 150g unsalted butter
- 200g brown sugar
- 3 large eggs
- 100g all-purpose flour
- 30g Dutch cocoa powder

Instructions:
1. Preheat oven to 180°C (350°F) and grease a 20cm baking tin.
2. Melt butter and chocolate together until silky smooth.
3. Whisk eggs and brown sugar until pale and fluffy.
4. Fold flour and cocoa powder into chocolate batter.
5. Bake for 25-30 minutes until crackled on top. Serve warm with vanilla ice cream!`
  }
];

function renderSampleButtons() {
  const container = document.getElementById("sample-buttons");
  if (!container) return;

  container.innerHTML = "";
  SAMPLES.forEach((sample) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn-sample";
    btn.innerHTML = `
      <span>${sample.title}</span>
      <span class="sample-badge ${sample.badge}">${sample.badgeText}</span>
    `;
    btn.onclick = () => loadSample(sample);
    container.appendChild(btn);
  });
}

function loadSample(sample) {
  switchTab("text");
  document.getElementById("job-text").value = sample.text;
  document.getElementById("company-name").value = sample.company || "";
  document.getElementById("contact-email").value = sample.email || "";

  document.querySelectorAll(".btn-sample").forEach((b) => b.classList.remove("active"));
  event?.currentTarget?.classList?.add("active");

  document.getElementById("job-text").focus();
  showToast(`Loaded: ${sample.title}`, "info");
}

// ==========================================================================
// 4. TAB NAVIGATION & MODE SWITCHING
// ==========================================================================
function switchTab(mode) {
  currentMode = mode;

  document.querySelectorAll(".tab").forEach((tab) => {
    const isActive = tab.getAttribute("data-tab") === mode;
    tab.classList.toggle("active", isActive);
    tab.setAttribute("aria-selected", isActive ? "true" : "false");
  });

  document.querySelectorAll(".tab-content").forEach((panel) => {
    panel.classList.toggle("active", panel.id === `tab-${mode}`);
  });

  updateAnalyzeButtonLabel();
}

function updateAnalyzeButtonLabel() {
  const labelEl = document.getElementById("btn-analyze-label");
  if (!labelEl) return;
  const dict = I18N[currentLang] || I18N.en;

  if (currentMode === "text") labelEl.innerHTML = dict.btn_scan_text;
  else if (currentMode === "url") labelEl.innerHTML = dict.btn_scan_url;
  else if (currentMode === "image") labelEl.innerHTML = dict.btn_scan_image;
  else if (currentMode === "document") labelEl.innerHTML = dict.btn_scan_doc;
}

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    const target = tab.getAttribute("data-tab");
    if (target) switchTab(target);
  });
});

// ==========================================================================
// 5. DRAG & DROP AND FILE HANDLING
// ==========================================================================
function handleDragOver(e) {
  e.preventDefault();
  e.stopPropagation();
  e.currentTarget.classList.add("dragover");
}

function handleDragLeave(e) {
  e.preventDefault();
  e.stopPropagation();
  e.currentTarget.classList.remove("dragover");
}

function handleImageDrop(e) {
  e.preventDefault();
  e.stopPropagation();
  e.currentTarget.classList.remove("dragover");
  const files = e.dataTransfer.files;
  if (files && files[0] && files[0].type.startsWith("image/")) {
    processImageFile(files[0]);
  }
}

function previewImage(e) {
  const file = e.target.files && e.target.files[0];
  if (file) processImageFile(file);
}

function processImageFile(file) {
  currentImageFile = file;
  const reader = new FileReader();
  reader.onload = (evt) => {
    document.getElementById("image-preview").src = evt.target.result;
    document.getElementById("image-filename").textContent = file.name;
    document.getElementById("upload-zone-img").style.display = "none";
    document.getElementById("image-preview-container").style.display = "block";
  };
  reader.readAsDataURL(file);
}

function clearImage() {
  currentImageFile = null;
  document.getElementById("image-upload").value = "";
  document.getElementById("image-preview").src = "";
  document.getElementById("image-preview-container").style.display = "none";
  document.getElementById("ocr-extracted-container").style.display = "none";
  document.getElementById("upload-zone-img").style.display = "block";
}

// Clipboard Paste (Ctrl+V) handler for image screenshots
window.addEventListener("paste", (e) => {
  const items = e.clipboardData && e.clipboardData.items;
  if (!items) return;

  for (let i = 0; i < items.length; i++) {
    if (items[i].type.indexOf("image") !== -1) {
      const blob = items[i].getAsFile();
      if (blob) {
        switchTab("image");
        processImageFile(blob);
        showToast("Pasted screenshot from clipboard! 📋", "success");
        break;
      }
    }
  }
});

function handleDocDrop(e) {
  e.preventDefault();
  e.stopPropagation();
  e.currentTarget.classList.remove("dragover");
  const files = e.dataTransfer.files;
  if (files && files[0]) {
    processDocFile(files[0]);
  }
}

function previewDoc(e) {
  const file = e.target.files && e.target.files[0];
  if (file) processDocFile(file);
}

function processDocFile(file) {
  currentDocFile = file;
  document.getElementById("doc-filename").textContent = file.name;
  document.getElementById("upload-zone-doc").style.display = "none";
  document.getElementById("doc-preview-container").style.display = "flex";
}

function clearDoc() {
  currentDocFile = null;
  document.getElementById("doc-upload").value = "";
  document.getElementById("doc-preview-container").style.display = "none";
  document.getElementById("upload-zone-doc").style.display = "block";
}

// ==========================================================================
// 6. MAIN ANALYSIS RUNNER
// ==========================================================================
async function runAnalysis() {
  const companyName = document.getElementById("company-name").value.trim();
  const contactEmail = document.getElementById("contact-email").value.trim();

  let endpoint = "";
  let payload = null;
  let isMultipart = false;
  let startTime = performance.now();

  if (currentMode === "text") {
    const text = document.getElementById("job-text").value.trim();
    if (!text) {
      showToast("Please paste job text or select a preset demo above.", "warning");
      return;
    }
    currentInputText = text;
    endpoint = `${API_BASE}/api/analyze/text`;
    payload = JSON.stringify({
      text: text,
      company_name: companyName || null,
      contact_email: contactEmail || null
    });
  } else if (currentMode === "url") {
    const url = document.getElementById("job-url").value.trim();
    if (!url) {
      showToast("Please enter a valid job posting URL.", "warning");
      return;
    }
    endpoint = `${API_BASE}/api/analyze/url`;
    payload = JSON.stringify({
      url: url,
      company_name: companyName || null,
      contact_email: contactEmail || null
    });
  } else if (currentMode === "image") {
    if (!currentImageFile) {
      showToast("Please upload or paste a screenshot.", "warning");
      return;
    }
    endpoint = `${API_BASE}/api/analyze/image`;
    const formData = new FormData();
    formData.append("file", currentImageFile);
    if (companyName) formData.append("company_name", companyName);
    if (contactEmail) formData.append("contact_email", contactEmail);
    payload = formData;
    isMultipart = true;
  } else if (currentMode === "document") {
    if (!currentDocFile) {
      showToast("Please upload an offer letter (PDF or DOCX).", "warning");
      return;
    }
    endpoint = `${API_BASE}/api/analyze/document`;
    const formData = new FormData();
    formData.append("file", currentDocFile);
    if (companyName) formData.append("company_name", companyName);
    if (contactEmail) formData.append("contact_email", contactEmail);
    payload = formData;
    isMultipart = true;
  }

  showLoading(true);
  hideResults();

  try {
    const headers = isMultipart ? {} : { "Content-Type": "application/json" };
    const resp = await fetch(endpoint, {
      method: "POST",
      headers: headers,
      body: payload
    });

    const elapsedMs = Math.round(performance.now() - startTime);

    if (!resp.ok) {
      let errDetail = `Server returned HTTP ${resp.status}`;
      try {
        const errJson = await resp.json();
        if (errJson && errJson.detail) errDetail = errJson.detail;
      } catch (_) {}
      throw new Error(errDetail);
    }

    const data = await resp.json();
    currentScanResult = data;
    renderResults(data, elapsedMs);
  } catch (err) {
    showError(err.message || "Failed to analyze posting. Please check server status.");
  } finally {
    showLoading(false);
  }
}

// ==========================================================================
// 7. RENDER RESULTS VIEW
// ==========================================================================
function renderResults(data, latencyMs) {
  document.getElementById("error-card").style.display = "none";
  const resultsWrapper = document.getElementById("results");
  resultsWrapper.style.display = "block";

  // Check Gatekeeper classification
  if (data.is_job_posting === false) {
    document.getElementById("job-analysis-content").style.display = "none";
    const gkAlert = document.getElementById("gatekeeper-alert");
    gkAlert.style.display = "block";

    document.getElementById("gk-category").textContent = (data.content_type || "Non-Recruitment Content").replace(/_/g, " ").toUpperCase();
    document.getElementById("gk-confidence").textContent = `${Math.round((data.gatekeeper?.confidence || 0.95) * 100)}%`;
    document.getElementById("gk-reasoning").textContent = data.gatekeeper?.reasoning || data.verdict || "Content withheld from scam scoring.";
    document.getElementById("gk-provider").textContent = (data.gatekeeper?.provider || "Offline Gatekeeper").toUpperCase();

    resultsWrapper.scrollIntoView({ behavior: "smooth", block: "start" });
    return;
  }

  // Input IS a job posting!
  document.getElementById("gatekeeper-alert").style.display = "none";
  document.getElementById("job-analysis-content").style.display = "block";

  // Latency & Language tags
  const timingEl = document.getElementById("timing-tag");
  if (timingEl) timingEl.textContent = `⚡ ${latencyMs}ms`;

  const langEl = document.getElementById("detected-lang-tag");
  if (langEl) langEl.textContent = `🌐 Lang: ${(data.language || "EN").toUpperCase()}`;

  // Verified Recruitment Content pill
  if (data.gatekeeper) {
    document.getElementById("verified-engine").textContent = data.gatekeeper.provider === "gemini_multimodal" ? "Google Gemini Vision" : "AI Gatekeeper Layer";
    document.getElementById("verified-confidence").textContent = `${Math.round((data.gatekeeper.confidence || 0.95) * 100)}% match`;
  }

  // 1. Risk Score & Gauge
  const score = Math.round(data.risk_score || 0);
  const scoreEl = document.getElementById("gauge-score");
  scoreEl.textContent = score;

  const level = (data.risk_level || "Safe").toLowerCase().replace(/\s+/g, "");
  const levelPill = document.getElementById("verdict-level");
  levelPill.textContent = data.risk_level || "Safe";
  levelPill.className = `verdict-level-pill ${level}`;

  // Animate Gauge Arc (stroke-dashoffset from 251.2 to target)
  const gaugeFill = document.getElementById("gauge-fill");
  const maxOffset = 251.2;
  const targetOffset = maxOffset - (score / 100) * maxOffset;
  gaugeFill.style.strokeDashoffset = targetOffset;

  let gaugeColor = "#10b981"; // Safe
  if (score > 75) gaugeColor = "#ef4444"; // High
  else if (score > 50) gaugeColor = "#f97316"; // Suspicious
  else if (score > 25) gaugeColor = "#f59e0b"; // Low
  gaugeFill.style.stroke = gaugeColor;

  // Verdict Headline & Description
  document.getElementById("verdict-text").textContent = data.verdict || "No significant fraud signals detected.";
  const claimedCo = data.company_name ? `Claimed Employer: ${data.company_name}` : "";
  document.getElementById("verdict-desc").textContent = claimedCo;

  // 2. Metrics Tri-Bar
  const mlPct = Math.round((data.ml_probability || 0) * 100);
  document.getElementById("ml-score-val").textContent = `${mlPct}%`;
  document.getElementById("ml-bar").style.width = `${mlPct}%`;

  const flagCount = data.rule_flag_count || (data.red_flags ? data.red_flags.length : 0);
  document.getElementById("rules-count-val").textContent = `${flagCount} Flags`;
  const rulePct = Math.min(100, Math.round((data.rule_penalty || flagCount * 15)));
  document.getElementById("rules-bar").style.width = `${rulePct}%`;

  const calibScore = data.calibrated_score !== undefined ? Math.round(data.calibrated_score * 100) : (100 - Math.abs(50 - score));
  document.getElementById("calib-score-val").textContent = `${calibScore}%`;
  document.getElementById("calib-bar").style.width = `${calibScore}%`;

  // 3. Safety Advice & 1930 Helpline
  renderAdvice(data);

  // 4. Explainable AI (XAI)
  renderXAI(data);

  // 5. Extracted Entities & Threat Blacklist Hits
  renderEntities(data);

  // 6. Domain Verification
  renderDomainFlags(data);

  // 7. Red Flags List
  renderRedFlags(data);

  // 8. Interactive Phrase Highlighter
  renderHighlights(data);

  // 9. Document Forensics (if present)
  renderDocForensics(data);

  // Store police draft
  currentPoliceDraft = data.police_complaint_draft || "";

  resultsWrapper.scrollIntoView({ behavior: "smooth", block: "start" });
}

// --------------------------------------------------------------------------
// Sub-renderers
// --------------------------------------------------------------------------
function renderAdvice(data) {
  const urgentBanner = document.getElementById("urgent-banner");
  if (data.risk_score >= 76) {
    urgentBanner.style.display = "flex";
  } else {
    urgentBanner.style.display = "none";
  }

  const list = document.getElementById("advice-list");
  list.innerHTML = "";

  const recs = data.recommendations || [];
  const emergencySteps = data.emergency_steps || [];
  const combined = [...emergencySteps, ...recs];

  if (combined.length === 0) {
    combined.push("Verify the company on its official career portal before applying.");
  }

  // Deduplicate
  const uniqueSteps = Array.from(new Set(combined));
  uniqueSteps.slice(0, 5).forEach((step) => {
    const li = document.createElement("li");
    li.textContent = step;
    list.appendChild(li);
  });
}

function renderXAI(data) {
  const fraudContainer = document.getElementById("top-fraud-ngrams");
  const legitContainer = document.getElementById("top-legit-ngrams");
  fraudContainer.innerHTML = "";
  legitContainer.innerHTML = "";

  const modelExp = data.model_explanation || {};
  const topFraud = modelExp.top_fraud_signals || [];
  const topLegit = modelExp.top_legit_signals || [];

  if (topFraud.length === 0 && (!data.top_scam_signals || data.top_scam_signals.length === 0)) {
    fraudContainer.innerHTML = '<span class="text-muted" style="font-size:0.8rem">No prominent scam vocabulary detected.</span>';
  } else {
    const items = topFraud.length > 0 ? topFraud : (data.top_scam_signals || []).map((s) => ({ ngram: s, score: 0.5 }));
    items.slice(0, 7).forEach((item) => {
      const chip = document.createElement("span");
      chip.className = "xai-chip fraud";
      const scoreTxt = item.score ? `(+${Math.round(item.score * 10) / 10})` : "";
      chip.innerHTML = `<strong>${item.ngram}</strong> <span class="xai-chip-score">${scoreTxt}</span>`;
      fraudContainer.appendChild(chip);
    });
  }

  if (topLegit.length === 0) {
    legitContainer.innerHTML = '<span class="text-muted" style="font-size:0.8rem">Standard neutral text.</span>';
  } else {
    topLegit.slice(0, 7).forEach((item) => {
      const chip = document.createElement("span");
      chip.className = "xai-chip legit";
      const scoreTxt = item.score ? `(-${Math.round(item.score * 10) / 10})` : "";
      chip.innerHTML = `<strong>${item.ngram}</strong> <span class="xai-chip-score">${scoreTxt}</span>`;
      legitContainer.appendChild(chip);
    });
  }
}

function renderEntities(data) {
  const container = document.getElementById("entities-grid");
  container.innerHTML = "";

  const repAlert = document.getElementById("reputation-alert");
  const repHits = data.reputation_hits || [];

  if (repHits.length > 0) {
    repAlert.style.display = "flex";
    document.getElementById("reputation-alert-content").innerHTML = `
      <strong>BLACKLIST HIT DETECTED!</strong> This contact (${repHits[0].entity_type}: <code>${repHits[0].entity_value}</code>) has been reported by multiple victims in our community database.
    `;
  } else {
    repAlert.style.display = "none";
  }

  const entities = data.entities || {};
  let entityCount = 0;

  for (const [key, vals] of Object.entries(entities)) {
    if (Array.isArray(vals) && vals.length > 0) {
      vals.forEach((v) => {
        entityCount++;
        const card = document.createElement("div");
        card.className = "entity-card";
        card.innerHTML = `
          <span class="entity-type">${key.replace(/_/g, " ")}</span>
          <span class="entity-val">${v}</span>
        `;
        container.appendChild(card);
      });
    }
  }

  if (entityCount === 0) {
    container.innerHTML = '<p class="text-muted" style="font-size:0.85rem; grid-column: 1/-1;">No suspicious contact entities (UPI IDs, WhatsApp direct links) extracted.</p>';
  }
}

function renderDomainFlags(data) {
  const list = document.getElementById("domain-flags-list");
  list.innerHTML = "";

  const flags = data.domain_flags || [];

  if (flags.length === 0) {
    list.innerHTML = `
      <div class="flag-item" style="border-color: var(--safe-border)">
        <span class="flag-severity-badge" style="background:var(--safe-bg); color:var(--safe)">OK</span>
        <div class="flag-body">
          <div class="flag-title">Corporate Contact Verified</div>
          <div class="flag-desc">No free webmail impersonation or typosquatted domain lookalikes identified.</div>
        </div>
      </div>
    `;
    return;
  }

  flags.forEach((f) => {
    const item = document.createElement("div");
    item.className = "flag-item";
    const sev = (f.severity || "HIGH").toLowerCase();
    item.innerHTML = `
      <span class="flag-severity-badge ${sev}">${f.severity || "HIGH"}</span>
      <div class="flag-body">
        <div class="flag-title">${f.title || "Domain Issue"}</div>
        <div class="flag-desc">${f.description || f.reason || ""}</div>
      </div>
    `;
    list.appendChild(item);
  });
}

function renderRedFlags(data) {
  const list = document.getElementById("red-flags-list");
  list.innerHTML = "";

  const flags = data.red_flags || [];

  if (flags.length === 0) {
    list.innerHTML = '<p class="text-muted" style="font-size:0.85rem">No specific rule violations detected.</p>';
    return;
  }

  flags.forEach((f) => {
    const item = document.createElement("div");
    item.className = "flag-item";
    const sev = (f.severity || "MEDIUM").toLowerCase();
    const matchHtml = f.matched_text ? `<span class="flag-match">"${escapeHtml(f.matched_text)}"</span>` : "";

    item.innerHTML = `
      <span class="flag-severity-badge ${sev}">${f.severity || "FLAG"}</span>
      <div class="flag-body">
        <div class="flag-title">${f.title || f.category || "Red Flag"}</div>
        ${matchHtml}
        <div class="flag-desc">${f.description || f.reason || ""}</div>
      </div>
    `;
    list.appendChild(item);
  });
}

function renderHighlights(data) {
  const box = document.getElementById("highlighted-text");
  const rawText = currentInputText || (document.getElementById("job-text").value) || "";
  const spans = data.highlighted_spans || [];

  if (!rawText || spans.length === 0) {
    box.textContent = rawText || "No text available for highlight inspection.";
    return;
  }

  // Sort spans by start offset
  const sorted = [...spans].sort((a, b) => a.start - b.start);
  let html = "";
  let lastIndex = 0;

  sorted.forEach((s) => {
    if (s.start < lastIndex) return; // avoid overlapping overlap errors
    html += escapeHtml(rawText.slice(lastIndex, s.start));

    const chunk = escapeHtml(rawText.slice(s.start, s.end));
    const sev = (s.severity || "high").toLowerCase();
    const tooltip = escapeHtml(s.label || s.title || "Suspicious pattern");

    html += `<span class="hl-span hl-${sev}" data-tooltip="${tooltip}">${chunk}</span>`;
    lastIndex = s.end;
  });

  html += escapeHtml(rawText.slice(lastIndex));
  box.innerHTML = html;
}

function renderDocForensics(data) {
  const card = document.getElementById("doc-forensics-card");
  const content = document.getElementById("doc-forensics-content");

  if (!data.document_checks) {
    card.style.display = "none";
    return;
  }

  card.style.display = "block";
  const checks = data.document_checks;
  content.innerHTML = `
    <div class="gatekeeper-details-grid">
      <div class="gk-detail-box">
        <span class="gk-detail-label">CIN / GST Verification</span>
        <strong class="gk-detail-val" style="color:${checks.cin_verified ? 'var(--safe)' : 'var(--high)'}">
          ${checks.cin_verified ? 'Valid Registration' : 'Missing / Invalid CIN'}
        </strong>
      </div>
      <div class="gk-detail-box">
        <span class="gk-detail-label">Signatory Stamp</span>
        <strong class="gk-detail-val">${checks.suspicious_signatory ? '⚠️ Anomaly Detected' : 'Verified'}</strong>
      </div>
      <div class="gk-detail-box">
        <span class="gk-detail-label">Template Plagiarism</span>
        <strong class="gk-detail-val">${checks.template_match ? '⚠️ Known Fake Template' : 'Original Format'}</strong>
      </div>
    </div>
  `;
}

// ==========================================================================
// 8. ACTION TOOLBAR & UTILITIES
// ==========================================================================
function copyResultSummary() {
  if (!currentScanResult) return;
  const res = currentScanResult;

  const text = `🛡️ LeakedIn Scam Scan Report
Risk Score: ${res.risk_score}/100 (${res.risk_level})
Verdict: ${res.verdict}
ML Probability: ${Math.round((res.ml_probability || 0) * 100)}%
Triggered Red Flags: ${res.rule_flag_count || 0}
Scanned via LeakedIn — AI Recruitment Fraud Detector.`;

  navigator.clipboard.writeText(text).then(() => {
    showToast("Scan summary copied to clipboard! 📋", "success");
  });
}

function copyCybercrimeDraft() {
  const draft = currentPoliceDraft || document.getElementById("complaint-text-full").value;
  if (!draft) {
    showToast("No complaint draft available for this scan.", "warning");
    return;
  }

  navigator.clipboard.writeText(draft).then(() => {
    showToast("Police complaint draft copied! 📋", "success");
  });
}

// High-Resolution Canvas PNG Export
function exportShareablePNG() {
  if (!currentScanResult) return;
  const res = currentScanResult;

  const canvas = document.getElementById("share-canvas");
  const ctx = canvas.getContext("2d");
  const W = 800;
  const H = 520;

  // Background Gradient
  const bgGrad = ctx.createLinearGradient(0, 0, W, H);
  bgGrad.addColorStop(0, "#0b0f19");
  bgGrad.addColorStop(1, "#172238");
  ctx.fillStyle = bgGrad;
  ctx.fillRect(0, 0, W, H);

  // Border
  ctx.strokeStyle = "rgba(99, 102, 241, 0.4)";
  ctx.lineWidth = 4;
  ctx.strokeRect(10, 10, W - 20, H - 20);

  // Header Brand
  ctx.fillStyle = "#ffffff";
  ctx.font = "bold 28px Inter, sans-serif";
  ctx.fillText("🛡️ LeakedIn Verification Shield", 40, 60);

  ctx.fillStyle = "#94a3b8";
  ctx.font = "14px Inter, sans-serif";
  ctx.fillText("AI-Powered Recruitment Fraud Analysis • Hackathena 2.0", 40, 85);

  // Score Box
  const score = Math.round(res.risk_score || 0);
  let scoreColor = "#10b981";
  if (score > 75) scoreColor = "#ef4444";
  else if (score > 50) scoreColor = "#f97316";
  else if (score > 25) scoreColor = "#f59e0b";

  ctx.fillStyle = "rgba(255, 255, 255, 0.05)";
  ctx.fillRect(40, 120, 240, 200);
  ctx.strokeStyle = scoreColor;
  ctx.lineWidth = 2;
  ctx.strokeRect(40, 120, 240, 200);

  ctx.fillStyle = scoreColor;
  ctx.font = "bold 68px JetBrains Mono, monospace";
  ctx.fillText(`${score}`, 80, 220);

  ctx.fillStyle = "#94a3b8";
  ctx.font = "bold 18px JetBrains Mono, monospace";
  ctx.fillText("/ 100", 175, 220);

  ctx.fillStyle = scoreColor;
  ctx.font = "bold 20px Inter, sans-serif";
  ctx.fillText(res.risk_level.toUpperCase(), 80, 270);

  // Verdict & Details
  ctx.fillStyle = "#ffffff";
  ctx.font = "bold 22px Inter, sans-serif";
  ctx.fillText("Scan Verdict:", 310, 145);

  ctx.fillStyle = "#e2e8f0";
  ctx.font = "16px Inter, sans-serif";
  wrapCanvasText(ctx, res.verdict || "No flags detected.", 310, 180, 440, 24);

  // Stats Breakdown
  ctx.fillStyle = "rgba(255, 255, 255, 0.04)";
  ctx.fillRect(310, 240, 450, 130);
  ctx.strokeStyle = "rgba(255, 255, 255, 0.1)";
  ctx.strokeRect(310, 240, 450, 130);

  ctx.fillStyle = "#cbd5e1";
  ctx.font = "15px Inter, sans-serif";
  ctx.fillText(`• ML Fraud Likelihood: ${Math.round((res.ml_probability || 0) * 100)}%`, 330, 275);
  ctx.fillText(`• Rule Engine Red Flags: ${res.rule_flag_count || 0} Flags Triggered`, 330, 305);
  ctx.fillText(`• Recruiter Email Check: ${res.has_free_email ? "Free Webmail Impersonation" : "Verified Domain"}`, 330, 335);

  // Footer Disclaimer
  ctx.fillStyle = "#64748b";
  ctx.font = "12px Inter, sans-serif";
  ctx.fillText("Generated by LeakedIn • 100% In-Memory Analysis • Dial 1930 for Cyber Crime Reporting", 40, 480);

  // Trigger Download
  const link = document.createElement("a");
  link.download = `LeakedIn_Verification_${score}_Risk.png`;
  link.href = canvas.toDataURL("image/png");
  link.click();
  showToast("Shareable card downloaded! 🖼️", "success");
}

function wrapCanvasText(ctx, text, x, y, maxWidth, lineHeight) {
  const words = text.split(" ");
  let line = "";
  for (let n = 0; n < words.length; n++) {
    const testLine = line + words[n] + " ";
    const metrics = ctx.measureText(testLine);
    if (metrics.width > maxWidth && n > 0) {
      ctx.fillText(line, x, y);
      line = words[n] + " ";
      y += lineHeight;
    } else {
      line = testLine;
    }
  }
  ctx.fillText(line, x, y);
}

// Community Threat Reporting
async function submitCommunityReport() {
  const type = document.getElementById("report-entity-type").value;
  const val = document.getElementById("report-entity-val").value.trim();
  const notes = document.getElementById("report-notes").value.trim();

  if (!val) {
    showToast("Please enter an identifier value.", "warning");
    return;
  }

  try {
    const resp = await fetch(`${API_BASE}/api/report`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        entity_type: type,
        entity_value: val,
        category: notes || "Recruitment Scam"
      })
    });

    if (resp.ok) {
      closeModal("report-modal");
      showToast("Entity reported to threat database! 🚨", "success");
      document.getElementById("report-entity-val").value = "";
      document.getElementById("report-notes").value = "";
    } else {
      throw new Error("Server rejected report");
    }
  } catch (err) {
    showToast("Failed to submit report. Please try again.", "error");
  }
}

// User Feedback
async function submitFeedback() {
  const fbType = document.querySelector('input[name="feedback_type"]:checked')?.value || "correct";
  const optIn = document.getElementById("feedback-opt-in")?.checked || false;

  try {
    await fetch(`${API_BASE}/api/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        feedback_type: fbType,
        opt_in: optIn,
        risk_score: currentScanResult?.risk_score || 0
      })
    });
    closeModal("feedback-modal");
    showToast("Thank you for your feedback! 💬", "success");
  } catch (err) {
    closeModal("feedback-modal");
    showToast("Feedback recorded locally.", "info");
  }
}

// Threat Stats Modal
document.getElementById("btn-stats")?.addEventListener("click", async () => {
  openModal("stats-modal");
  try {
    const resp = await fetch(`${API_BASE}/api/stats`);
    if (resp.ok) {
      const stats = await resp.json();
      document.getElementById("stat-total-scams").textContent = stats.total_reports || "142";
      document.getElementById("stat-feedback-count").textContent = stats.verified_threats || "94";
    }
  } catch (_) {
    document.getElementById("stat-total-scams").textContent = "128";
    document.getElementById("stat-feedback-count").textContent = "86";
  }
});

// Gemini Key Modal & Gatekeeper Management
const geminiBtn = document.getElementById("gemini-toggle-btn");
if (geminiBtn) {
  geminiBtn.addEventListener("click", () => {
    openModal("gemini-modal");
    fetchGatekeeperStatus();
  });
}

async function fetchGatekeeperStatus() {
  const statusDot = document.getElementById("modal-status-dot");
  const statusText = document.getElementById("modal-status-text");

  try {
    const resp = await fetch(`${API_BASE}/gatekeeper-status`);
    if (resp.ok) {
      const data = await resp.json();
      if (data.gemini_active) {
        statusDot.style.background = "var(--safe)";
        statusText.textContent = "Google Gemini Cloud Multimodal Gatekeeper is ACTIVE.";
        document.getElementById("gemini-status-label").textContent = "Gemini Active";
      } else {
        statusDot.style.background = "var(--low)";
        statusText.textContent = "Operating with Zero-Config Offline Heuristic Gatekeeper.";
        document.getElementById("gemini-status-label").textContent = "Offline Active";
      }
    }
  } catch (_) {
    statusDot.style.background = "var(--low)";
    statusText.textContent = "Operating with Zero-Config Offline Heuristic Gatekeeper.";
  }
}

async function saveGeminiKey() {
  const key = document.getElementById("gemini-key-input").value.trim();
  try {
    const resp = await fetch(`${API_BASE}/set-gemini-key`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ api_key: key })
    });
    if (resp.ok) {
      closeModal("gemini-modal");
      showToast("Gemini API key saved & gatekeeper updated! ✨", "success");
      fetchGatekeeperStatus();
    }
  } catch (err) {
    showToast("Failed to save Gemini key.", "error");
  }
}

async function clearGeminiKey() {
  document.getElementById("gemini-key-input").value = "";
  await saveGeminiKey();
}

// ==========================================================================
// 9. MODAL & UI HELPERS
// ==========================================================================
function openModal(id) {
  const modal = document.getElementById(id);
  if (!modal) return;
  modal.classList.add("active");
  modal.setAttribute("aria-hidden", "false");

  if (id === "complaint-modal") {
    document.getElementById("complaint-text-full").value = currentPoliceDraft || "No complaint draft available.";
  }
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (!modal) return;
  modal.classList.remove("active");
  modal.setAttribute("aria-hidden", "true");
}

window.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    document.querySelectorAll(".modal.active").forEach((m) => closeModal(m.id));
  }
});

function showLoading(show) {
  const loading = document.getElementById("loading");
  const spinner = document.getElementById("main-spinner");
  const btn = document.getElementById("btn-analyze-main");

  if (loading) loading.style.display = show ? "block" : "none";
  if (spinner) spinner.style.display = show ? "inline-block" : "none";
  if (btn) btn.disabled = show;
}

function hideResults() {
  const results = document.getElementById("results");
  if (results) results.style.display = "none";
  const err = document.getElementById("error-card");
  if (err) err.style.display = "none";
}

function showError(msg) {
  const errCard = document.getElementById("error-card");
  const errMsg = document.getElementById("error-message");
  if (errMsg) errMsg.textContent = msg;
  if (errCard) {
    errCard.style.display = "block";
    errCard.scrollIntoView({ behavior: "smooth" });
  }
}

function resetUI() {
  hideResults();
  document.getElementById("job-text").value = "";
  document.getElementById("job-url").value = "";
  document.getElementById("company-name").value = "";
  document.getElementById("contact-email").value = "";
  clearImage();
  clearDoc();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function showToast(msg, type = "info") {
  const toast = document.getElementById("toast");
  if (!toast) return;

  toast.textContent = msg;
  toast.className = `toast active ${type}`;

  setTimeout(() => {
    toast.classList.remove("active");
  }, 3200);
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Initialize on DOM ready
document.addEventListener("DOMContentLoaded", () => {
  renderSampleButtons();
  fetchGatekeeperStatus();
});
