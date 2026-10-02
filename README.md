# OttoMeet – Microsoft-Teams-App für Besprechungen

OttoMeet erscheint in einer Teams-Besprechung als **eigenes Symbol in der Meeting-Leiste**:

```text
Chat · Personen · Heben · Reagieren · Ansicht · Notizen · Räume · [OttoMeet] · Apps · Weitere · Kamera · Mikro · Teilen
```

Ein Klick öffnet rechts das **OttoMeet-Side-Panel** mit den Reitern *Meeting*, *Zusammenfassung* und *Einstellungen*:

| Status (vom OttoMeet-Backend) | Anzeige | Buttons |
|---|---|---|
| Einwilligung fehlt | 🟡 **Consent erforderlich** | **Consent geben** · Transkript starten (OttoMeet öffnen) |
| Einwilligung erteilt (auch Opt-out-Meeting oder automatische Einwilligung) | 🟢 **Consent erteilt** · „Transkription aktiv“ mit Laufzeit | **Consent ablehnen** · Transkript starten (OttoMeet öffnen) |
| Einwilligung abgelehnt | 🔴 **Consent abgelehnt** | **Consent geben** · Transkript starten (OttoMeet öffnen) |
| OttoMeet läuft in diesem Meeting nicht | ⚪ **OttoMeet ist nicht aktiv** | Consent geben (ausgegraut) · Transkript starten (OttoMeet öffnen) |

- **Consent geben / Consent ablehnen** öffnen den bestehenden OttoMeet-Einwilligungsablauf im Browser
  (Anmeldung mit dem Microsoft-Konto, Bestätigung, Audit-Eintrag, Mikrofon-Freigabe bzw. -Sperre).
- **Transkript starten (OttoMeet öffnen)** öffnet OttoMeet – vorerst als Platzhalter `https://www.google.de`,
  später die HTTPS-Adresse, die in die OttoMeet-Windows-App weiterleitet.
- Der Status wird alle 10 Sekunden aktualisiert, nach einem Klick für 2 Minuten alle 3 Sekunden.

### Live

| | |
|---|---|
| Web-App | <https://qavion-consulting.github.io/meeting-ai-ms-panel/> |
| GitHub-Repository | [QAVION-CONSULTING/meeting-ai-ms-panel](https://github.com/QAVION-CONSULTING/meeting-ai-ms-panel) |
| Teams-App-Paket | `ottomeet-app/dist/ottomeet-teams-app.zip` (nach `python3 build.py`) |

> Die früheren Varianten *Meeting Links Panel* und *Meeting Links Stage* liegen unter `archiv/`
> und werden nicht mehr verwendet. Das Repository `meeting-ai-ms-stage` wird nicht mehr benötigt.

---

## Inhalt

1. [Was geht – und was nicht](#1-was-geht--und-was-nicht)
2. [So funktioniert es](#2-so-funktioniert-es)
3. [Voraussetzungen](#3-voraussetzungen)
4. [Projektstruktur](#4-projektstruktur)
5. [Einstellungen](#5-einstellungen)
6. [OttoMeet-Backend anbinden](#6-ottomeet-backend-anbinden)
7. [Web-App veröffentlichen (HTTPS-Hosting)](#7-web-app-veröffentlichen-https-hosting)
8. [Teams-App-Paket bauen](#8-teams-app-paket-bauen)
9. [In Teams hochladen und freigeben](#9-in-teams-hochladen-und-freigeben)
10. [OttoMeet in die Meeting-Leiste bringen](#10-ottomeet-in-die-meeting-leiste-bringen)
11. [Im Meeting verwenden](#11-im-meeting-verwenden)
12. [Updates einspielen](#12-updates-einspielen)
13. [Fehlerbehebung](#13-fehlerbehebung)
14. [Technische Details und Ausbaustufen](#14-technische-details-und-ausbaustufen)

---

## 1. Was geht – und was nicht

| Wunsch | Möglich? | Umsetzung |
|---|---|---|
| Eigenes OttoMeet-Symbol in der Meeting-Leiste | ✅ | Meeting-App mit `meetingSidePanel`. Erscheint, sobald die App zum Meeting hinzugefügt ist ([Abschnitt 10](#10-ottomeet-in-die-meeting-leiste-bringen)). |
| Side Panel mit Consent-Status und Buttons | ✅ | Diese App. |
| Status „Consent erteilt“ / „abgelehnt“ anzeigen | ✅ | Benötigt die Backend-Route `/teams/app-status` ([Abschnitt 6](#6-ottomeet-backend-anbinden)). |
| App automatisch in jedem OttoMeet-Meeting | ✅ | Optionaler Backend-Baustein `install_meeting_tab.py` (Graph). |
| Roter Badge am App-Symbol | ❌ | Teams bietet dafür nach aktuellem Stand keine Schnittstelle. |
| Einblendung „Zustimmung erforderlich“ im Meeting | ⚠️ nur mit Bot | *Targeted In-Meeting Notification* über einen Bot – Ausbaustufe, siehe [Abschnitt 14](#14-technische-details-und-ausbaustufen). |

---

## 2. So funktioniert es

```text
 Teams-Meeting                    GitHub Pages                         OttoMeet-Backend
┌──────────────────┐   lädt   ┌──────────────────────┐   fetch    ┌─────────────────────────────┐
│ [OttoMeet] Symbol│ ───────▶ │ Side Panel (HTML/JS) │ ─────────▶ │ GET /teams/app-status       │
│  → Side Panel    │          │ index.html, app.js   │            │   → Consent-Status (JSON)   │
└──────────────────┘          └──────────┬───────────┘            │                             │
                                         │ Browser öffnen         │ GET /teams/consent-entry    │
                                         └──────────────────────▶ │   → 302 /teams/consent …    │
                                                                  │   → Entra-Login, Audit,     │
                                                                  │     Rechte-Sync (bestehend) │
                                                                  └─────────────────────────────┘
```

- Das **Teams-App-Paket** (ZIP) enthält nur Manifest und Icons. Die Oberfläche ist eine Webseite auf GitHub Pages.
- Die App kennt aus Teams die **Chat-ID des Meetings** (`context.chat.id` = `consent_sessions.chat_id`)
  und die **Entra-Objekt-ID / UPN** der Person.
- Einwilligung, Audit-Trail, Teams-Rollen und Mikrofon-Sperre bleiben **vollständig im OttoMeet-Backend**.

---

## 3. Voraussetzungen

| Was | Wofür |
|---|---|
| **Python 3** | Build-Skript `build.py` (nur Standardbibliothek) |
| **GitHub-Repository mit Pages** (oder Azure Static Web Apps) | Hosting der Web-App – bereits eingerichtet |
| **OttoMeet-Backend** mit den neuen Routen | Status und Consent-Buttons ([Abschnitt 6](#6-ottomeet-backend-anbinden)) |
| **Teams-Administrator** | App freigeben ([Abschnitt 9](#9-in-teams-hochladen-und-freigeben)) |

---

## 4. Projektstruktur

```text
ms-plugin/
├─ README.md                          <- diese Datei
├─ ottomeet-app/                      <- die Teams-App
│  ├─ settings.json                   <- HIER Backend-URL, Texte, Version einstellen
│  ├─ build.py                        <- baut dist/
│  ├─ appPackage/
│  │  ├─ manifest.template.json       <- Teams-Manifest v1.16 (meetingSidePanel)
│  │  ├─ color.png   (192×192, „OM“)
│  │  └─ outline.png (32×32)
│  ├─ web/
│  │  ├─ index.html, app.js, styles.css  <- Side Panel
│  │  ├─ config.js                    <- wird beim Build aus settings.json erzeugt
│  │  ├─ config.html                  <- Einrichtungsseite beim Hinzufügen zum Meeting
│  │  ├─ privacy.html, terms.html
│  │  └─ vendor/MicrosoftTeams.min.js  (TeamsJS 2.57.0)
│  └─ tools/make_icons.py             <- erzeugt die Icons neu
├─ ottomeet-backend/                  <- Bausteine für das OttoMeet-Backend (FastAPI)
│  ├─ README.md                       <- Schnittstellen-Beschreibung
│  ├─ consent_entry_route.py          <- GET /teams/consent-entry
│  ├─ app_status_route.py             <- GET /teams/app-status
│  └─ install_meeting_tab.py          <- optional: App automatisch ins Meeting
└─ archiv/                            <- frühere Varianten (nicht mehr verwendet)
```

Nach dem Build:

```text
ottomeet-app/dist/
├─ ottomeet-teams-app.zip   -> in Teams hochladen
└─ web/                     -> auf GitHub Pages veröffentlichen
```

> **Nur `ottomeet-teams-app.zip` in Teams hochladen.** Den Ordner `dist/` nicht selbst komprimieren –
> sonst meldet Teams *„ManifestFileNotFound: No manifest.json file in the zip package“*.

---

## 5. Einstellungen

`ottomeet-app/settings.json`:

```json
{
  "appId": "a41253e6-0f12-4524-97e8-c93b22afded7",
  "version": "1.0.0",
  "host": "https://qavion-consulting.github.io/meeting-ai-ms-panel",
  "developerName": "QAVION Consulting",
  "backendUrl": "https://YOUR_OTTOMEET_BACKEND",
  "statusPollSeconds": 10,
  "labels": {
    "consent": "Consent geben",
    "withdraw": "Consent ablehnen",
    "ottomeet": "Transkript starten (OttoMeet öffnen)"
  },
  "ottomeetUrl": "https://www.google.de"
}
```

| Feld | Bedeutung |
|---|---|
| `appId` | ID der Teams-App. **Nie ändern** – Teams erkennt Updates daran. |
| `version` | Version im Format `1.0.0`. Nur bei Manifest-Änderungen erhöhen. |
| `host` | Adresse der Web-App (GitHub Pages), ohne `/` am Ende. |
| `developerName` | Herausgeber in Teams. |
| `backendUrl` | Öffentliche Basis-URL des OttoMeet-Backends (`BACKEND_URL_FRONTEND`). Solange der Platzhalter drinsteht, zeigt die App „Consent erforderlich“ ohne echten Status, und die Buttons melden „Backend noch nicht konfiguriert“. |
| `statusPollSeconds` | Abstand der Status-Abfrage in Sekunden (mindestens 5). |
| `labels` | Beschriftungen der drei Buttons. |
| `ottomeetUrl` | Ziel von **Transkript starten (OttoMeet öffnen)**. Leer (`""`) blendet den Button aus. |

Backend-URL setzen und gleich speichern:

```bash
cd ottomeet-app
python3 build.py --backend https://ottomeet.deutz.com --save
```

---

## 6. OttoMeet-Backend anbinden

Im Ordner [`ottomeet-backend/`](ottomeet-backend/README.md) liegen fertige FastAPI-Bausteine.
Die mit `# adapt` markierten Zeilen verweisen auf vorhandene Funktionen (Sitzung per `chat_id`,
letzte Entscheidung, persistente Einwilligung, Token der Datenschutz-Karte).

| Baustein | Zweck | Pflicht |
|---|---|---|
| `GET /teams/consent-entry?chat_id=…&act=accept\|decline` | Buttons **Consent geben** / **Consent ablehnen**: sucht die laufende Sitzung und leitet auf `/teams/consent` bzw. `/teams/withdraw_consent` weiter | ja |
| `GET /teams/app-status?chat_id=…&user_oid=…&upn=…` | Status-Karte im Side Panel (JSON) | ja |
| CORS für `https://qavion-consulting.github.io` | nötig, weil das Side Panel `/teams/app-status` per `fetch` abfragt | ja |
| `install_ottomeet_tab(token, chat_id)` | fügt OttoMeet beim Start automatisch zum Meeting hinzu → Symbol in der Leiste für alle | optional |

Nach dem Einbau: `backendUrl` setzen ([Abschnitt 5](#5-einstellungen)), bauen, Web-App veröffentlichen.
**Kein neues Teams-ZIP nötig** – die Backend-URL steckt nur in den Web-Dateien.

---

## 7. Web-App veröffentlichen (HTTPS-Hosting)

Teams lädt das Side Panel von einer öffentlichen HTTPS-Adresse. Anforderungen: HTTPS, ohne Login
erreichbar, Einbetten in Teams erlaubt (kein `X-Frame-Options: DENY/SAMEORIGIN`, kein
`frame-ancestors 'self'`). GitHub Pages und Azure Static Web Apps erfüllen das.

### Variante A – GitHub Pages (aktuell im Einsatz)

| | |
|---|---|
| Repository | [QAVION-CONSULTING/meeting-ai-ms-panel](https://github.com/QAVION-CONSULTING/meeting-ai-ms-panel) (öffentlich, Branch `main`, Ordner `/`) |
| Adresse | `https://qavion-consulting.github.io/meeting-ai-ms-panel` |
| Seiten | [index.html](https://qavion-consulting.github.io/meeting-ai-ms-panel/index.html) · [config.html](https://qavion-consulting.github.io/meeting-ai-ms-panel/config.html) · [privacy.html](https://qavion-consulting.github.io/meeting-ai-ms-panel/privacy.html) · [terms.html](https://qavion-consulting.github.io/meeting-ai-ms-panel/terms.html) |

Außerhalb von Teams zeigt die Seite *„Nur in einer Teams-Besprechung verfügbar“* – das ist normal.

**Veröffentlichen / aktualisieren** (im Ordner `ms-plugin/`):

```bash
cd ottomeet-app && python3 build.py && cd ..
rm -rf /tmp/meeting-ai-ms-panel
git clone git@github.com:QAVION-CONSULTING/meeting-ai-ms-panel.git /tmp/meeting-ai-ms-panel
rsync -a --delete --exclude .git ottomeet-app/dist/web/ /tmp/meeting-ai-ms-panel/
(cd /tmp/meeting-ai-ms-panel && git add -A && git commit -m "OttoMeet Update" && git push)
```

Ohne Terminal: im Repository **Add file → Upload files** → alle Dateien und den Ordner `vendor`
aus `ottomeet-app/dist/web/` hineinziehen → **Commit changes**.

GitHub Pages braucht 1–3 Minuten (Status unter **Actions**). `build.py` hängt an alle Skript- und
Style-Verweise einen Versionsstempel (`app.js?v=…`), damit Teams nach einem Update nicht alte,
zwischengespeicherte Dateien verwendet.

**Einmalige Einrichtung (erledigt):** Repository öffentlich anlegen → Dateien hochladen →
**Settings → Pages → Deploy from a branch → main / (root) → Save**.

### Variante B – Azure Static Web Apps (kostenlos, für Firmen mit Azure)

**Voraussetzung:** Azure-Abonnement (Plan *Free* kostet nichts) und [Node.js](https://nodejs.org) für `npx`.

1. [Azure-Portal](https://portal.azure.com) → **Static Web Apps** → **+ Erstellen**
   - Ressourcengruppe wählen oder anlegen (z. B. `rg-ottomeet`), Name `ottomeet-teams`
   - Plantyp **Free**, Quelle **Other** → **Überprüfen und erstellen → Erstellen**
2. URL notieren (**Übersicht → URL**), z. B. `https://nice-sea-0123abc.2.azurestaticapps.net`.
3. Mit dieser Adresse bauen:
   ```bash
   cd ottomeet-app
   python3 build.py --host https://<azure-url> --version 1.0.1 --save
   ```
4. **Übersicht → Bereitstellungstoken verwalten** → Token kopieren, dann hochladen:
   ```bash
   npx @azure/static-web-apps-cli deploy ./dist/web --deployment-token <TOKEN> --env production
   ```
5. Prüfen: `https://<azure-url>/index.html`.
6. Weil sich die Adresse ändert: neues `dist/ottomeet-teams-app.zip` in Teams hochladen und freigeben lassen.

**Ohne Node.js:** Static Web App mit Quelle **GitHub** anlegen und `meeting-ai-ms-panel` wählen
(App location `/`, Output location leer) – Azure veröffentlicht dann bei jedem Push automatisch.

**Eigene Domain:** **Benutzerdefinierte Domänen → + Hinzufügen** (z. B. `ottomeet-teams.deutz.com`),
danach wie Schritt 3 und 6.

| | GitHub Pages | Azure Static Web Apps |
|---|---|---|
| Kosten | kostenlos | kostenlos (Plan *Free*) |
| Repository öffentlich | ja | nein |
| Upload | Git oder Browser | `npx …` oder automatisch über GitHub |
| Eigene Domain | möglich | möglich, mit automatischem Zertifikat |
| Empfehlung | Test / Pilot | dauerhafter Firmeneinsatz |

---

## 8. Teams-App-Paket bauen

```bash
cd ottomeet-app
python3 build.py
```

| Option | Wirkung |
|---|---|
| `--backend https://…` | OttoMeet-Backend-URL setzen |
| `--host https://…` | Adresse der Web-App ändern (z. B. beim Wechsel auf Azure) |
| `--version 1.0.1` | neue Version für Manifest-Updates |
| `--save` | Optionen dauerhaft in `settings.json` speichern |

Ergebnis: `dist/ottomeet-teams-app.zip` (Manifest + Icons, ohne Ordner) und `dist/web/`.
Das Skript bricht ab, wenn Adressen nicht mit `https://` beginnen.

---

## 9. In Teams hochladen und freigeben

### App einreichen (ohne Admin-Rechte)

Teams → **Apps** → **Apps verwalten** → **App hochladen** → **App an Ihre Organisation übermitteln**
→ `ottomeet-app/dist/ottomeet-teams-app.zip`.
Die App steht dann unter **Ausstehende Anfragen** mit Status *Ausstehend*.

> Die alten Anfragen **Meeting Links Panel** und **Meeting Links Stage** dort über das Papierkorb-Symbol
> löschen – sie werden nicht mehr gebraucht.

### Admin: freigeben

1. [Teams Admin Center](https://admin.teams.microsoft.com) → **Teams-Apps → [Apps verwalten](https://admin.teams.microsoft.com/policies/manage-apps)**.
2. Kachel **„Ausstehende Genehmigung“** → **OttoMeet** auswählen
   (oder Filter **Veröffentlichungsstatus = Übermittelt**).
3. **Veröffentlichungsstatus → Veröffentlichen**.
4. Prüfen: Status **Zulässig**, Verfügbarkeit **Jeder** (oder die gewünschten Gruppen).

Alternativ lädt der Admin das ZIP direkt hoch: **Teams-Apps → Apps verwalten → Hochladen** – dann ist
es sofort veröffentlicht.

### Nur für dich testen (Sideloading)

**Apps → Apps verwalten → App hochladen → Benutzerdefinierte App hochladen**. Fehlt der Punkt, muss der
Admin unter **Teams-Apps → Setuprichtlinien → Global** *Benutzerdefinierte Apps hochladen* einschalten.

---

## 10. OttoMeet in die Meeting-Leiste bringen

Das OttoMeet-Symbol erscheint in der Meeting-Leiste, **sobald die App zum Meeting hinzugefügt** ist.
Dafür gibt es drei Wege:

**a) Automatisch durch das OttoMeet-Backend (empfohlen)**
Beim Start der Aufzeichnung ruft das Backend `install_ottomeet_tab(organizer_token, chat_id)` auf
([`ottomeet-backend/install_meeting_tab.py`](ottomeet-backend/install_meeting_tab.py)). Die App wird im
Meeting-Chat installiert und als Tab hinzugefügt – das Symbol erscheint für alle Teilnehmer.
Voraussetzungen: App ist im Admin Center veröffentlicht; zusätzliche Graph-Berechtigungen
`TeamsAppInstallation.ReadWriteForChat` und `TeamsTab.Create`.

**b) Durch den Organisator vor dem Meeting**
Besprechung im Kalender öffnen → **+** (App hinzufügen) → **OttoMeet** → **Speichern**.

**c) Im laufenden Meeting**
**Apps** in der Leiste → **OttoMeet** → **Hinzufügen** → **Speichern**.

**Anheften:** Teams zeigt nur wenige Apps direkt in der Leiste, weitere landen unter **Weitere**.
Eine App lässt sich per Rechtsklick auf das Symbol → **Anheften** dauerhaft sichtbar machen.
Admins können OttoMeet zusätzlich in **Teams-Apps → Setuprichtlinien** unter *Installierte Apps* und
*Angeheftete Apps* aufnehmen; wie stark das die Meeting-Leiste beeinflusst, hängt von der Teams-Version ab –
zuverlässig ist Weg a).

---

## 11. Im Meeting verwenden

1. **OttoMeet** in der Meeting-Leiste anklicken → das Side Panel öffnet sich.
2. **Consent erforderlich** → **Consent geben** → im Browser mit dem Microsoft-Konto anmelden → bestätigen.
   Nach wenigen Sekunden zeigt das Panel **Consent erteilt ✓** und **Transkription aktiv**; das Mikrofon ist frei.
3. **Consent ablehnen** (nur sichtbar nach Einwilligung) → im Browser bestätigen → Status **Consent abgelehnt**,
   das Mikrofon wird gesperrt.
4. **Transkript starten (OttoMeet öffnen)** öffnet OttoMeet.

Die Datenschutz-Karte im Meeting-Chat funktioniert weiterhin parallel – beide Wege schreiben in denselben Audit-Trail.

---

## 12. Updates einspielen

| Änderung | Vorgehen |
|---|---|
| Backend-URL, Button-Texte, OttoMeet-Link, Design, Logik (`settings.json` außer `host`/`version`, Dateien in `web/`) | `python3 build.py` → `dist/web` veröffentlichen ([Abschnitt 7](#7-web-app-veröffentlichen-https-hosting)). **Kein** neues ZIP, **keine** neue Freigabe. |
| Name, Beschreibung, Icons, `host`, Manifest | `python3 build.py --version 1.0.1 --save` → `dist/web` veröffentlichen **und** neues ZIP einreichen → Admin veröffentlicht das Update. |

---

## 13. Fehlerbehebung

| Problem | Ursache / Lösung |
|---|---|
| `ManifestFileNotFound` beim Upload | Falsches ZIP. Nur `ottomeet-app/dist/ottomeet-teams-app.zip` verwenden. |
| OttoMeet nicht in der Meeting-Leiste | App nicht zum Meeting hinzugefügt ([Abschnitt 10](#10-ottomeet-in-die-meeting-leiste-bringen)) oder unter **Weitere** – dort anheften. Nur geplante Besprechungen mit Chat; Kanal-Besprechungen werden nicht unterstützt. |
| App im Store nicht auffindbar | Noch nicht vom Admin veröffentlicht, oder Verfügbarkeit nicht für dich freigegeben. |
| Side Panel bleibt weiß | Web-App nicht erreichbar: `https://qavion-consulting.github.io/meeting-ai-ms-panel/index.html` im Browser prüfen. |
| „Status derzeit nicht verfügbar“ | Backend nicht erreichbar, Route `/teams/app-status` fehlt oder **CORS** für `https://qavion-consulting.github.io` nicht gesetzt (Browser-Konsole zeigt dann einen CORS-Fehler). |
| „Backend noch nicht konfiguriert“ | `backendUrl` in `settings.json` setzen, bauen, veröffentlichen. |
| „OttoMeet ist nicht aktiv“ | In diesem Meeting wurde OttoMeet noch nicht gestartet (keine offene Sitzung für diese Chat-ID). |
| Status springt nach Einwilligung nicht um | Bestätigung im Browser nicht abgeschlossen (zweiter Schritt `confirm=1`). Panel neu öffnen – es lädt den Status sofort neu. |
| Nach Update alte Oberfläche | 1–3 Minuten auf GitHub Pages warten, dann Side Panel schließen und neu öffnen. |

---

## 14. Technische Details und Ausbaustufen

**Aktuell**
- Manifest v1.16, konfigurierbarer Tab in `groupChat` mit den Kontexten `meetingSidePanel`,
  `meetingChatTab`, `meetingDetailsTab`. Keine zusätzlichen Berechtigungen im Manifest.
- TeamsJS 2.57.0 lokal eingebunden; Links werden über `microsoftTeams.app.openLink` geöffnet.
- Status-Abfrage `GET /teams/app-status` mit `chat_id`, `user_oid`, `upn` aus dem TeamsJS-Kontext.
  Diese Werte sind **nicht kryptografisch geprüft** – sie steuern nur die *Anzeige*. Die Einwilligung
  selbst läuft immer über die Entra-Anmeldung auf `/teams/consent`.
- Unterstützt helles, dunkles und kontrastreiches Teams-Design.

**Ausbaustufe 1 – Teams-SSO für den Status**
Statt `user_oid`/`upn` als Parameter: `microsoftTeams.authentication.getAuthToken()` im Side Panel, Token im
`Authorization`-Header, Prüfung im Backend. Benötigt eine Entra-App-Registrierung mit
„API verfügbar machen“ (`api://qavion-consulting.github.io/meeting-ai-ms-panel/<client-id>`) und
`webApplicationInfo` im Manifest (neue Version + Freigabe).

**Ausbaustufe 2 – Consent direkt im Panel**
Mit SSO kann das Panel die Einwilligung ohne Browserfenster direkt an das Backend senden
(neue Route, gleiche Audit- und Rechte-Logik wie `confirm=1`).

**Ausbaustufe 3 – Einblendung „Zustimmung erforderlich“ im Meeting**
Über einen Bot (Azure Bot Service) mit *Targeted In-Meeting Notification*: Das Backend sendet beim Start
eine Benachrichtigung nur an Teilnehmer ohne Einwilligung, mit Link auf das Side Panel. Benötigt
Bot-Registrierung, `bots` im Manifest und die RSC-Berechtigung `OnlineMeetingNotification.Send.Chat`.
Ein roter Badge am App-Symbol ist damit nicht möglich.

Microsoft-Dokumentation:
- [Apps für Teams-Besprechungen](https://learn.microsoft.com/de-de/microsoftteams/platform/apps-in-teams-meetings/teams-apps-in-meetings)
- [Meeting-Side-Panel](https://learn.microsoft.com/de-de/microsoftteams/platform/apps-in-teams-meetings/build-tabs-for-meeting)
- [In-Meeting-Benachrichtigungen](https://learn.microsoft.com/de-de/microsoftteams/platform/apps-in-teams-meetings/in-meeting-notification-for-meeting)
- [Apps im Teams Admin Center verwalten](https://learn.microsoft.com/de-de/microsoftteams/manage-apps)
- [App-Setuprichtlinien](https://learn.microsoft.com/de-de/microsoftteams/teams-app-setup-policies)
