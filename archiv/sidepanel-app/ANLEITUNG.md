# Meeting Links Panel – Teams-App für das Side Panel

Die App zeigt in einer Teams-Besprechung zwei HTTPS-Buttons im **Side Panel** (rechter Bereich)
an. Jeder Teilnehmer öffnet die App für sich selbst; ein Klick öffnet den Link nur für ihn.
Die Buttons sind **I Consent** (OttoMeet-Einwilligung, benötigt die Backend-Route aus
[`../ottomeet-backend/`](../ottomeet-backend/README.md)) und **Open OttoMeet** (vorerst `https://www.google.de`).

Kein Backend, kein Bot, keine Azure-App-Registrierung nötig.

## Aufbau

```text
sidepanel-app/
├─ settings.json                  <- HIER alles einstellen (Host, Buttons, Version)
├─ build.py                       <- baut dist/
├─ appPackage/
│  ├─ manifest.template.json      <- Teams-Manifest v1.16 (Kontext: meetingSidePanel)
│  ├─ color.png  (192x192)
│  └─ outline.png (32x32)
├─ web/
│  ├─ index.html, app.js, styles.css, config.js
│  ├─ config.html                 <- Einrichtungsseite beim Hinzufügen zum Meeting
│  ├─ privacy.html, terms.html
│  └─ vendor/MicrosoftTeams.min.js (TeamsJS 2.57.0, lokal)
└─ tools/make_icons.py
```

Nach dem Build:

```text
dist/
├─ meeting-links-panel-teams-app.zip   <- das installierbare Teams-App-Paket
└─ web/                                <- dieser Inhalt kommt auf den Webserver
```

Das Teams-ZIP enthält nur `manifest.json` und Icons. Die Oberfläche ist eine Webseite, die Teams
per **HTTPS** lädt – deshalb muss `dist/web` zuerst auf einem Webserver liegen.

## Schritt 1 – Web-App hosten

Der Server muss statische Dateien per HTTPS ausliefern und darf das Einbetten nicht verbieten
(kein `X-Frame-Options: DENY/SAMEORIGIN`, kein `frame-ancestors 'self'`).

- **Azure Static Web Apps** (kostenlos): Portal → *Static Web Apps* → *Erstellen* → Plan *Free*, Bereitstellung *Other*.
  Hochladen: `npx @azure/static-web-apps-cli deploy dist/web --deployment-token <TOKEN> --env production`
- **GitHub Pages**: Inhalt von `dist/web` in ein Repository, *Settings → Pages*. URL: `https://<benutzer>.github.io/<repo>`
- **Eigener Server** (IIS, nginx, Apache) mit gültigem TLS-Zertifikat.

## Schritt 2 – Einstellungen

`settings.json`:

```json
{
  "appId": "427a407a-b0ca-4bd2-afb4-a5b102659403",
  "version": "1.0.0",
  "host": "https://meetinglinks-panel.meinefirma.de",
  "developerName": "Meine Firma GmbH",
  "title": "Meeting Links",
  "subtitle": "Schnellzugriff während der Besprechung",
  "consent":  { "label": "I Consent",     "backendUrl": "https://YOUR_OTTOMEET_BACKEND" },
  "ottomeet": { "label": "Open OttoMeet", "url": "https://www.google.de" }
}
```

- `host` = Adresse aus Schritt 1, ohne `/` am Ende.
- `appId` **nicht ändern** – Teams erkennt Updates an dieser ID.
- Alle URLs müssen mit `https://` beginnen.

## Schritt 3 – Bauen und hochladen

```bash
cd sidepanel-app
python3 build.py --host https://meetinglinks-panel.meinefirma.de --save
```

1. **Inhalt** von `dist/web/` auf den Webserver hochladen.
2. Im Browser prüfen: `https://<host>/index.html` zeigt die zwei Buttons, `https://<host>/config.html` lädt.

## Schritt 4 – In Teams installieren

**Nur für dich testen:** Teams → **Apps** → **Apps verwalten** → **App hochladen** →
**Benutzerdefinierte App hochladen** → `dist/meeting-links-panel-teams-app.zip`.

**Für die ganze Organisation:** [Teams Admin Center](https://admin.teams.microsoft.com) →
**Teams-Apps → Apps verwalten → Hochladen** → ZIP auswählen.

Fehlt „Benutzerdefinierte App hochladen“: Admin aktiviert im Teams Admin Center unter
*Teams-Apps → Setuprichtlinien → Global* **Benutzerdefinierte Apps hochladen** (kann bis zu 24 h dauern).

## Schritt 5 – Im Meeting verwenden

1. Geplante Besprechung öffnen oder im laufenden Meeting oben auf **Apps / +** klicken.
2. **Meeting Links Panel** suchen → **Hinzufügen** → **Speichern**.
3. Im Meeting oben auf das App-Symbol klicken → das Side Panel öffnet sich mit
   **I Consent** und **Open OttoMeet**.

## Updates

- **Nur Buttons/Texte/Design geändert:** `python3 build.py`, `dist/web` neu hochladen – fertig.
- **Host, Name oder Icons geändert:** `version` erhöhen (z. B. `1.0.1`), `python3 build.py`,
  ZIP in Teams bzw. im Admin Center über **Aktualisieren** neu hochladen.

## Fehlerbehebung

| Problem | Lösung |
|---|---|
| „Benutzerdefinierte App hochladen“ fehlt | Admin muss das Hochladen erlauben (Schritt 4). |
| Side Panel bleibt weiß | `dist/web` fehlt auf dem Server oder Server sendet `X-Frame-Options`. `https://<host>/index.html` im Browser prüfen. |
| App im Meeting nicht auffindbar | Nur in geplanten Besprechungen mit Chat; Kanal-Besprechungen werden nicht unterstützt. |
| Buttons öffnen nichts | Popups blockiert oder URL nicht `https://`. |
