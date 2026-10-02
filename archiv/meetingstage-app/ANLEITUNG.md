# Meeting Links Stage – Teams-App für die Meeting Stage

Die App zeigt zwei HTTPS-Buttons groß auf der **Meeting-Bühne (Stage)** an – für alle Teilnehmer
gleichzeitig sichtbar. Die Buttons sind **I Consent** (OttoMeet-Einwilligung, benötigt die Backend-Route aus
[`../ottomeet-backend/`](../ottomeet-backend/README.md)) und **Open OttoMeet** (vorerst `https://www.google.de`).
Ein Klick gilt immer nur für die Person, die klickt.

Kein Backend, kein Bot, keine Azure-App-Registrierung nötig.

### Warum hat die Stage-App trotzdem ein Side Panel?

Microsoft Teams erlaubt das Teilen einer App auf die Bühne **nur aus ihrem eigenen Side Panel heraus**
(API `meeting.shareAppContentToStage`). Das Manifest braucht dafür beide Kontexte
`meetingSidePanel` und `meetingStage` sowie die Berechtigung `MeetingStage.Write.Chat`.
Das Side Panel dieser App enthält deshalb **nur** den Button „Auf Meeting-Bühne anzeigen“;
die eigentlichen Links erscheinen ausschließlich auf der Bühne.

## Aufbau

```text
meetingstage-app/
├─ settings.json                  <- HIER alles einstellen (Host, Buttons, Version)
├─ build.py                       <- baut dist/
├─ appPackage/
│  ├─ manifest.template.json      <- Teams-Manifest v1.16 (meetingSidePanel + meetingStage)
│  ├─ color.png  (192x192, petrol)
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
├─ meeting-links-stage-teams-app.zip   <- das installierbare Teams-App-Paket
└─ web/                                <- dieser Inhalt kommt auf den Webserver
```

Das Teams-ZIP enthält nur `manifest.json` und Icons. Die Oberfläche ist eine Webseite, die Teams
per **HTTPS** lädt – deshalb muss `dist/web` zuerst auf einem Webserver liegen.

## Schritt 1 – Web-App hosten

Der Server muss statische Dateien per HTTPS ausliefern und darf das Einbetten nicht verbieten
(kein `X-Frame-Options: DENY/SAMEORIGIN`, kein `frame-ancestors 'self'`).
Wenn du beide Apps nutzt, gib jeder eine **eigene Adresse** (eigene Subdomain oder eigener Unterpfad).

- **Azure Static Web Apps** (kostenlos): Portal → *Static Web Apps* → *Erstellen* → Plan *Free*, Bereitstellung *Other*.
  Hochladen: `npx @azure/static-web-apps-cli deploy dist/web --deployment-token <TOKEN> --env production`
- **GitHub Pages**: Inhalt von `dist/web` in ein Repository, *Settings → Pages*. URL: `https://<benutzer>.github.io/<repo>`
- **Eigener Server** (IIS, nginx, Apache) mit gültigem TLS-Zertifikat.

## Schritt 2 – Einstellungen

`settings.json`:

```json
{
  "appId": "275a1cc5-f9a8-40da-b11b-e1bd1ad6ede9",
  "version": "1.0.0",
  "host": "https://meetinglinks-stage.meinefirma.de",
  "developerName": "Meine Firma GmbH",
  "title": "Meeting Links",
  "subtitle": "Für alle Teilnehmer auf der Meeting-Bühne",
  "consent":  { "label": "I Consent",     "backendUrl": "https://YOUR_OTTOMEET_BACKEND" },
  "ottomeet": { "label": "Open OttoMeet", "url": "https://www.google.de" }
}
```

- `host` = Adresse aus Schritt 1, ohne `/` am Ende.
- `appId` **nicht ändern** – Teams erkennt Updates an dieser ID.
- Alle URLs müssen mit `https://` beginnen.

## Schritt 3 – Bauen und hochladen

```bash
cd meetingstage-app
python3 build.py --host https://meetinglinks-stage.meinefirma.de --save
```

1. **Inhalt** von `dist/web/` auf den Webserver hochladen.
2. Im Browser prüfen: `https://<host>/index.html` zeigt die Bühnenansicht mit den zwei Buttons,
   `https://<host>/config.html` lädt.

## Schritt 4 – In Teams installieren

**Nur für dich testen:** Teams → **Apps** → **Apps verwalten** → **App hochladen** →
**Benutzerdefinierte App hochladen** → `dist/meeting-links-stage-teams-app.zip`.

**Für die ganze Organisation:** [Teams Admin Center](https://admin.teams.microsoft.com) →
**Teams-Apps → Apps verwalten → Hochladen** → ZIP auswählen.

Fehlt „Benutzerdefinierte App hochladen“: Admin aktiviert im Teams Admin Center unter
*Teams-Apps → Setuprichtlinien → Global* **Benutzerdefinierte Apps hochladen** (kann bis zu 24 h dauern).

Beim Hinzufügen fragt Teams nach der Berechtigung **„Inhalte auf der Besprechungsbühne anzeigen“**
(`MeetingStage.Write.Chat`) – zustimmen.

## Schritt 5 – Auf die Bühne bringen

1. Geplante Besprechung öffnen oder im laufenden Meeting oben auf **Apps / +** klicken.
2. **Meeting Links Stage** suchen → **Hinzufügen** → **Speichern**.
3. Im laufenden Meeting oben auf das App-Symbol klicken → im Side Panel erscheint
   **Auf Meeting-Bühne anzeigen**.
4. Klicken → alle Teilnehmer sehen **I Consent** und **Open OttoMeet** groß auf der Bühne.
5. Beenden über **Freigabe beenden** in der Teams-Leiste.

Teilen dürfen nur **Organisator und Referenten**, und nur im **Teams-Desktop- oder Web-Client**
(nicht am Handy). Auf dem Handy sehen Teilnehmer die geteilte Bühne trotzdem.

## Updates

- **Nur Buttons/Texte/Design geändert:** `python3 build.py`, `dist/web` neu hochladen – fertig.
- **Host, Name oder Icons geändert:** `version` erhöhen (z. B. `1.0.1`), `python3 build.py`,
  ZIP in Teams bzw. im Admin Center über **Aktualisieren** neu hochladen.

## Fehlerbehebung

| Problem | Lösung |
|---|---|
| „Benutzerdefinierte App hochladen“ fehlt | Admin muss das Hochladen erlauben (Schritt 4). |
| Side Panel oder Bühne bleibt weiß | `dist/web` fehlt auf dem Server oder Server sendet `X-Frame-Options`. `https://<host>/index.html` im Browser prüfen. |
| „Auf Meeting-Bühne anzeigen“ ist ausgegraut | Du bist nicht Organisator/Referent oder nutzt die Mobil-App. |
| „Teilen fehlgeschlagen“ | Berechtigung beim Hinzufügen abgelehnt → App aus dem Meeting entfernen und neu hinzufügen. |
| App im Meeting nicht auffindbar | Nur in geplanten Besprechungen mit Chat; Kanal-Besprechungen werden nicht unterstützt. |
