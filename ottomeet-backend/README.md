# OttoMeet backend – additions for the OttoMeet Teams app

The Teams app (`ottomeet-app/`) is a meeting side panel. It needs two routes in the existing
OttoMeet backend; a third, optional helper adds the app to meetings automatically.

| File | Route / function | Required |
|---|---|---|
| [`consent_entry_route.py`](consent_entry_route.py) | `GET /teams/consent-entry` – buttons **Consent geben** / **Consent ablehnen** | yes |
| [`app_status_route.py`](app_status_route.py) | `GET /teams/app-status` – status card in the side panel | yes |
| [`install_meeting_tab.py`](install_meeting_tab.py) | `install_ottomeet_tab(token, chat_id)` – OttoMeet button appears in the meeting bar automatically | optional |

All marked `# adapt` lines point to existing helpers (session lookup by `chat_id`, latest decision,
persistent consent, card token builder).

## 1. `GET /teams/consent-entry`

```text
GET /teams/consent-entry?chat_id=<context.chat.id>&act=accept|decline
```

| Case | Response |
|---|---|
| Open session for `chat_id` | `302` → `/teams/consent?token=…` (`accept`) or `/teams/withdraw_consent?token=…` (`decline`), same signed token as the privacy card |
| No open session | `404` HTML "OttoMeet ist nicht aktiv" |

Opened in the browser by the Teams app (`app.openLink`), not via `fetch` – no CORS needed.
Everything after the redirect is the existing flow (Entra sign-in, confirmation with `confirm=1`,
`consents` row with ts/ip/UA/jti, chat notice, permission sync).

## 2. `GET /teams/app-status`

```text
GET /teams/app-status?chat_id=<context.chat.id>&user_oid=<context.user.id>&upn=<context.user.userPrincipalName>
```

Response when no session is open:

```json
{ "session_active": false }
```

Response with an open session:

```json
{
  "session_active": true,
  "recording_mode": "consent",
  "decision": "accept",
  "persistent_consent": false,
  "consented": true,
  "started_at": "2026-10-02T13:45:12+00:00"
}
```

| Field | Meaning |
|---|---|
| `decision` | Latest `consents` row of this user in this session: `accept`, `decline` or `none` |
| `consented` | Result of the eligibility rules (decline > tagged > accept > persistent) |
| `started_at` | `consent_sessions.created_at`, used for the timer in the side panel |

The side panel shows:

| Status | Card | Buttons |
|---|---|---|
| `session_active: false` | "OttoMeet ist nicht aktiv" | Consent geben (disabled), Transkript starten |
| `consented: false`, `decision: none` | "Consent erforderlich" (yellow) | **Consent geben**, Transkript starten |
| `decision: decline` | "Consent abgelehnt" (red) | **Consent geben**, Transkript starten |
| `consented: true` | "Consent erteilt ✓" (green), "Transkription aktiv" + timer | **Consent ablehnen**, Transkript starten |

**CORS is required**, because the side panel calls this route with `fetch()`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://qavion-consulting.github.io"],
    allow_methods=["GET"],
    allow_headers=["Accept"],
)
```

### Security note

`user_oid` and `upn` come from the TeamsJS context and are **not verified** – they only select which
status is *displayed*. Consent itself is never given through this route; it always goes through the
Entra sign-in on `/teams/consent`. The route reveals only the decision of the given user in the given
meeting chat. If that is too much, protect it with Teams SSO (`microsoftTeams.authentication.getAuthToken()`,
token validation in the backend, `webApplicationInfo` in the manifest) – see the main README, section 12.

## 3. Optional: add the app to every OttoMeet meeting

Call `install_ottomeet_tab(organizer_token, chat_id)` right after creating the consent session in
`start-recording-direct` and `start-recording-tagged-meeting`. It installs the app in the meeting chat
and adds the OttoMeet tab, so the **OttoMeet** button appears in the meeting bar for everyone.

Requirements:
- The app is **published** in the org catalog (Teams Admin Center).
- Additional delegated Graph scopes: `TeamsAppInstallation.ReadWriteForChat`, `TeamsTab.Create`.
- Failures are logged and ignored – the privacy card keeps working without the tab.
