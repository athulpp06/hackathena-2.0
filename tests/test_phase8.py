"""
test_phase8.py - Unit tests for Phase 8 distribution channels (Browser Extension).
Validates Manifest V3 structure, permissions, content scripts, and required assets.
"""

import json
from pathlib import Path


def test_chrome_extension_manifest():
    """Verify Manifest V3 file exists and contains valid JSON with required permissions."""
    manifest_path = Path("extension/manifest.json")
    assert manifest_path.exists(), "extension/manifest.json must exist"

    with open(manifest_path, encoding="utf-8") as f:
        data = json.load(f)

    assert data["manifest_version"] == 3
    assert "contextMenus" in data["permissions"]
    assert "storage" in data["permissions"]
    assert "background" in data
    assert "service_worker" in data["background"]
    assert data["background"]["service_worker"] == "background.js"


def test_chrome_extension_files_and_assets():
    """Verify all core extension scripts, popup views, and icon assets exist."""
    extension_dir = Path("extension")
    assert (extension_dir / "background.js").exists(), "background.js missing"
    assert (extension_dir / "content.js").exists(), "content.js missing"
    assert (extension_dir / "popup.html").exists(), "popup.html missing"
    assert (extension_dir / "popup.js").exists(), "popup.js missing"
    assert (extension_dir / "popup.css").exists(), "popup.css missing"

    for size in ["16", "32", "48", "128"]:
        icon_path = extension_dir / "icons" / f"icon{size}.png"
        assert icon_path.exists(), f"Icon {size} missing"
        assert icon_path.stat().st_size > 0, f"Icon {size} is empty"


def test_chrome_extension_content_scripts_and_hosts():
    """Verify content scripts match patterns target LinkedIn, Indeed, and Naukri."""
    manifest_path = Path("extension/manifest.json")
    with open(manifest_path, encoding="utf-8") as f:
        data = json.load(f)

    content_scripts = data.get("content_scripts", [])
    assert len(content_scripts) >= 1

    all_matches = []
    for cs in content_scripts:
        all_matches.extend(cs.get("matches", []))

    assert any("linkedin.com" in m for m in all_matches), "LinkedIn matcher missing"
    assert any("indeed.com" in m for m in all_matches), "Indeed matcher missing"
    assert any("naukri.com" in m for m in all_matches), "Naukri matcher missing"

    host_perms = data.get("host_permissions", [])
    assert any("8000" in h for h in host_perms), "Local backend host permission missing"
