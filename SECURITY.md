# Security Policy

## 🔒 Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| < 2.0   | :x:                |

---

## 🛡️ Reporting a Vulnerability

If you discover a security vulnerability in LeakedIn (such as an SSRF bypass in URL scraping, regex denial of service in multilingual heuristics, or sensitive data exposure), please report it responsibly:

1. **Do not** create a public GitHub issue.
2. Email the maintainers directly at [athulpp2006@gmail.com](mailto:athulpp2006@gmail.com) or use [GitHub Private Vulnerability Reporting](https://github.com/athulpp06/hackathena-2.0/security/advisories/new).
3. Include:
   - Detailed steps to reproduce the vulnerability
   - Potential impact and threat vector
   - Suggested remediation or patch (if known)

We will respond promptly to acknowledge, investigate, and release a security advisory and patch.

---

## 🛡️ Built-in Security Architecture

- **SSRF Defense**: The URL analyzer rejects loopback (`127.0.0.1`), link-local (`169.254.0.0/16`), private RFC 1918 subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), and AWS/GCP metadata endpoints (`169.254.169.254`).
- **Cryptographic Anonymity**: Contact entities submitted to `reputation.db` are hashed using HMAC SHA-256 with an environment salt (`REPUTATION_SALT`). Raw identifiers (emails, phone numbers, UPI IDs) are never retained.
- **In-Memory Analysis**: Text submissions, screenshots, and offer letters are processed strictly in RAM and discarded immediately after response generation.
- **Zero-Trust Input Sanitization**: DOM injections in frontend and browser extension use native DOM nodes and `textContent` to defend against XSS.
