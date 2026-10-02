#!/usr/bin/env python3
"""Baut das Teams-App-Paket und den Web-Ordner aus settings.json.

Aufruf:
    python3 build.py                                   # Werte aus settings.json
    python3 build.py --host https://meetinglinks.contoso.de
    python3 build.py --host https://user.github.io/meeting-links --version 1.0.1

Ergebnis:
    dist/meeting-links-panel-teams-app.zip   -> in Teams hochladen
    dist/web/                          -> Inhalt auf den HTTPS-Webserver hochladen
"""
from pathlib import Path
from urllib.parse import urlparse
import argparse
import json
import re
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parent
SETTINGS = ROOT / "settings.json"
TEMPLATE = ROOT / "appPackage" / "manifest.template.json"
WEB = ROOT / "web"
DIST = ROOT / "dist"


def fail(msg):
    sys.exit(f"Fehler: {msg}")


def require_https(url, name):
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        fail(f"{name} muss eine gültige https://-Adresse sein (ist: {url!r}).")
    return parsed


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", help="Öffentliche HTTPS-Basisadresse des Web-Ordners")
    parser.add_argument("--version", help="App-Version, z.B. 1.0.1 (für Updates erhöhen)")
    parser.add_argument("--save", action="store_true", help="--host/--version in settings.json speichern")
    args = parser.parse_args()

    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    if args.host:
        settings["host"] = args.host
    if args.version:
        settings["version"] = args.version

    host = settings["host"].rstrip("/")
    if "YOUR_HOST" in host:
        fail("Bitte zuerst die Host-Adresse setzen: python3 build.py --host https://deine-adresse --save")
    hostname = require_https(host, "host").hostname

    if not re.fullmatch(r"\d+\.\d+\.\d+", settings["version"]):
        fail("version muss das Format 1.0.0 haben.")
    if settings["ottomeet"]["url"]:
        require_https(settings["ottomeet"]["url"], "ottomeet.url")

    backend = settings["consent"]["backendUrl"].rstrip("/")
    if not backend or "YOUR_OTTOMEET_BACKEND" in backend:
        print("Hinweis: consent.backendUrl ist nicht gesetzt – der Button „I Consent“ zeigt einen Hinweis statt zu funktionieren.")
        backend = ""
    else:
        require_https(backend, "consent.backendUrl")

    manifest_text = TEMPLATE.read_text(encoding="utf-8")
    replacements = {
        "{{HOST}}": host,
        "{{HOSTNAME}}": hostname,
        "{{APP_ID}}": settings["appId"],
        "{{VERSION}}": settings["version"],
        "{{DEVELOPER_NAME}}": settings["developerName"],
    }
    for placeholder, value in replacements.items():
        manifest_text = manifest_text.replace(placeholder, json.dumps(value)[1:-1])
    manifest = json.loads(manifest_text)

    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(WEB, DIST / "web")

    web_config = {
        "title": settings["title"],
        "subtitle": settings["subtitle"],
        "consent": {"label": settings["consent"]["label"], "backendUrl": backend},
        "ottomeet": settings["ottomeet"],
    }
    (DIST / "web" / "config.js").write_text(
        "window.MEETING_LINKS_CONFIG = " + json.dumps(web_config, indent=2, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )

    zip_path = DIST / "meeting-links-panel-teams-app.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
        z.write(ROOT / "appPackage" / "color.png", "color.png")
        z.write(ROOT / "appPackage" / "outline.png", "outline.png")

    if args.save:
        SETTINGS.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Teams-App-Paket : {zip_path}")
    print(f"Web-Dateien     : {DIST / 'web'}  ->  hochladen nach {host}/")
    print(f"Prüfe vor dem Upload, dass {host}/index.html im Browser erreichbar ist.")


if __name__ == "__main__":
    main()
