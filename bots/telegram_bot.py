"""
telegram_bot.py - Telegram Bot interface for LeakedIn AI Scam Shield.

Users can forward suspicious messages, send job posting screenshots, or paste
links directly to this bot to receive instant threat analysis, red-flag breakdowns,
and next-step safety advice.

Requires:
    pip install python-telegram-bot>=20.0
Run with:
    $env:TELEGRAM_BOT_TOKEN="your_bot_token_from_botfather"
    python -m bots.telegram_bot
"""

import io
import os
import sys
import logging
from typing import Any

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Import the shared LeakedIn detection pipeline directly (No duplicated logic!)
from backend.app.api.routes import _run_pipeline
from backend.app.ocr import extract_text_from_image

logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("leakedin-bot")


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def format_telegram_report(res: dict[str, Any]) -> str:
    """Formats the unified detection result into a clean Telegram Markdown response."""
    score = res.get("risk_score", 0)
    level = res.get("risk_level", "Unknown")
    verdict = res.get("verdict", "")
    ml_prob = round(res.get("ml_score", 0.0) * 100)
    lang = (res.get("language", "en") or "en").upper()

    # Severity emoji
    if score > 75:
        icon = "🚨"
    elif score > 50:
        icon = "🟠"
    elif score > 25:
        icon = "🟡"
    else:
        icon = "✅"

    lines = [
        f"{icon} *LEAKEDIN SCAM AUDIT REPORT*",
        "━━━━━━━━━━━━━━━━━━━━",
        f"*Threat Score:* `{score}/100` ({level})",
        f"*ML Scam Likelihood:* `{ml_prob}%`",
        f"*Language Detected:* `{lang}`",
        f"*Verdict:* {verdict}",
        "",
    ]

    # Red Flags
    flags = res.get("rule_matches") or res.get("red_flags") or []
    if flags:
        lines.append("🚩 *Triggered Red Flags:*")
        for f in flags[:4]:
            category = f.get("category", "Flag")
            matched = f.get("matched_text")
            msg = f.get("description") or f.get("message") or ""
            term_str = f" (`{matched}`)" if matched else ""
            lines.append(f"• *{category}*{term_str}: {msg}")
        lines.append("")

    # Extracted Entities
    entities = res.get("entities") or {}
    entity_lines = []
    if entities.get("phones"):
        entity_lines.append(f"📞 Phone(s): {', '.join(entities['phones'])}")
    if entities.get("upi_ids"):
        entity_lines.append(f"💳 UPI ID(s): {', '.join(entities['upi_ids'])}")
    if entities.get("telegram_handles"):
        entity_lines.append(f"💬 Telegram: {', '.join(entities['telegram_handles'])}")

    if entity_lines:
        lines.append("🔎 *Extracted Identifiers:*")
        lines.extend(entity_lines)
        lines.append("")

    # Reputation DB Match
    reputation_hits = res.get("reputation_hits") or []
    if reputation_hits:
        lines.append("⛔ *COMMUNITY BLACKLIST HIT:*")
        for hit in reputation_hits:
            val = hit.get("entity_value") or hit.get("value")
            lines.append(f"• `{val}` was reported previously as a known scammer contact!")
        lines.append("")

    # Domain Findings
    domain_flags = res.get("domain_findings") or res.get("domain_flags") or []
    if domain_flags:
        lines.append("🌐 *Domain Verification:*")
        for df in domain_flags[:2]:
            lines.append(f"• {df}")
        lines.append("")

    # Safety Advice & Helplines
    advice = res.get("safety_advice") or {}
    if advice.get("urgent_actions"):
        lines.append("⚠️ *URGENT ACTION NEEDED:*")
        for action in advice["urgent_actions"]:
            lines.append(f"• {action}")
        lines.append("")
    elif advice.get("next_steps"):
        lines.append("💡 *Recommended Next Steps:*")
        for step in advice["next_steps"][:3]:
            lines.append(f"• {step}")
        lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("🛡️ *National Cyber Crime Helpline:* Dial *1930* or file at [cybercrime.gov.in](https://cybercrime.gov.in)")
    lines.append("🔒 _In-memory scan. Zero personal data stored._")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome instructions."""
    welcome = (
        "🛡️ *Welcome to LeakedIn AI Scam Shield!*\n\n"
        "I can protect you from fake job postings, advance-fee recruitment scams, "
        "and identity theft across India.\n\n"
        "*How to use me:*\n"
        "1. 📝 *Forward or paste* any suspicious job offer message or email.\n"
        "2. 📷 *Send a screenshot* of a WhatsApp, Telegram, or SMS chat.\n"
        "3. 🔗 *Send a job link* from LinkedIn, Indeed, or Naukri.\n\n"
        "_Tip: Never pay registration fees or share your Aadhaar/PAN before verified interviews!_"
    )
    if update.message:
        await update.message.reply_text(welcome, parse_mode=ParseMode.MARKDOWN)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help instructions."""
    help_text = (
        "💡 *LeakedIn Bot Commands & Help*\n\n"
        "/start - Welcome screen and instructions\n"
        "/help - How to use this bot\n"
        "/helpline - Official 1930 Indian cybercrime contact info\n\n"
        "Just send or forward any message or screenshot anytime to scan it."
    )
    if update.message:
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


async def helpline_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send emergency cybercrime helpline contacts."""
    contacts = (
        "🚨 *National Cyber Crime Reporting Portal (I4C)*\n\n"
        "• *Emergency Toll-Free Helpline:* `1930`\n"
        "• *Official Portal:* [cybercrime.gov.in](https://cybercrime.gov.in)\n"
        "• *Action for UPI / Bank Frauds:* Call 1930 within the golden hour (< 2 hours) to freeze stolen transaction funds.\n"
        "• *Action for Leaked Aadhaar:* Lock your biometrics immediately on UIDAI / mAadhaar app."
    )
    if update.message:
        await update.message.reply_text(contacts, parse_mode=ParseMode.MARKDOWN)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Analyze incoming text or forwarded messages."""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    if len(text) < 10:
        await update.message.reply_text("Please provide a longer message or job posting snippet to analyze.")
        return

    # Send typing action
    await update.message.reply_chat_action("typing")

    try:
        # Run shared pipeline
        result = _run_pipeline(text=text)
        reply = format_telegram_report(result)
        await update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
    except Exception as exc:
        logger.error("Error analyzing text: %s", exc)
        await update.message.reply_text(f"⚠️ Error scanning message: {str(exc)}")


async def handle_photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Download photo and run EasyOCR + detection pipeline."""
    if not update.message or not update.message.photo:
        return

    await update.message.reply_text("🔍 Screenshot received! Extracting text via offline OCR...")
    await update.message.reply_chat_action("typing")

    try:
        # Get highest resolution photo
        photo = update.message.photo[-1]
        file = await photo.get_file()
        photo_bytes = await file.download_as_bytearray()

        # Run OCR
        extracted_text = extract_text_from_image(bytes(photo_bytes))
        if not extracted_text or extracted_text.startswith("No text could be extracted"):
            await update.message.reply_text("⚠️ Could not detect readable text in that image. Please ensure text is clear or paste it directly.")
            return

        # Run pipeline
        result = _run_pipeline(text=extracted_text)
        reply = format_telegram_report(result)
        await update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
    except Exception as exc:
        logger.error("Error processing photo: %s", exc)
        await update.message.reply_text(f"⚠️ OCR or analysis error: {str(exc)}")


# ---------------------------------------------------------------------------
# Bot Entrypoint
# ---------------------------------------------------------------------------

def run_bot() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("\n" + "="*70)
        print("🚨 TELEGRAM_BOT_TOKEN environment variable is not set!")
        print("="*70)
        print("To run the LeakedIn Telegram Bot:")
        print("1. Message @BotFather on Telegram and send /newbot.")
        print("2. Copy your API HTTP token.")
        print("3. Run in your terminal:")
        print("   $env:TELEGRAM_BOT_TOKEN=\"your_bot_token_here\"  # PowerShell")
        print("   python -m bots.telegram_bot")
        print("="*70 + "\n")
        return

    logger.info("Initializing LeakedIn Telegram Bot...")
    app = Application.builder().token(token).build()

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("helpline", helpline_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo_message))

    logger.info("LeakedIn Bot is polling for updates. Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    run_bot()
