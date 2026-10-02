"""Optional: add the OttoMeet Teams app to a meeting automatically when a recording starts.

Once the app is installed in the meeting chat and has a tab, the OttoMeet button appears in the
meeting bar for every participant (no one has to add it manually under "Apps").

Call install_ottomeet_tab(organizer_token, chat_id) in start-recording-direct and
start-recording-tagged-meeting, right after the consent session has been created.
Errors are logged and ignored: the privacy card in the chat keeps working without the tab.

Additional delegated Graph scopes for the app registration:
    TeamsAppInstallation.ReadWriteForChat, TeamsTab.Create
"""
import logging

import requests

log = logging.getLogger(__name__)

GRAPH = "https://graph.microsoft.com/v1.0"
OTTOMEET_MANIFEST_ID = "a41253e6-0f12-4524-97e8-c93b22afded7"
OTTOMEET_CONTENT_URL = "https://qavion-consulting.github.io/meeting-ai-ms-panel/index.html"
TIMEOUT = 15


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _catalog_app_id(token: str) -> str | None:
    """The org catalog id differs from the manifest id; look it up via externalId."""
    r = requests.get(
        f"{GRAPH}/appCatalogs/teamsApps",
        params={"$filter": f"externalId eq '{OTTOMEET_MANIFEST_ID}'"},
        headers=_headers(token),
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    apps = r.json().get("value", [])
    return apps[0]["id"] if apps else None


def install_ottomeet_tab(token: str, chat_id: str) -> bool:
    try:
        app_id = _catalog_app_id(token)
        if not app_id:
            log.warning("OttoMeet app not found in the org app catalog (not published yet?)")
            return False
        app_bind = f"{GRAPH}/appCatalogs/teamsApps/{app_id}"

        r = requests.post(
            f"{GRAPH}/chats/{chat_id}/installedApps",
            json={"teamsApp@odata.bind": app_bind},
            headers=_headers(token),
            timeout=TIMEOUT,
        )
        if r.status_code not in (201, 409):  # 409 = already installed
            r.raise_for_status()

        tabs = requests.get(f"{GRAPH}/chats/{chat_id}/tabs", params={"$expand": "teamsApp"},
                            headers=_headers(token), timeout=TIMEOUT)
        tabs.raise_for_status()
        if any(t.get("teamsApp", {}).get("id") == app_id for t in tabs.json().get("value", [])):
            return True

        r = requests.post(
            f"{GRAPH}/chats/{chat_id}/tabs",
            json={
                "displayName": "OttoMeet",
                "teamsApp@odata.bind": app_bind,
                "configuration": {
                    "entityId": "ottomeet",
                    "contentUrl": OTTOMEET_CONTENT_URL,
                    "websiteUrl": OTTOMEET_CONTENT_URL,
                },
            },
            headers=_headers(token),
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        return True
    except requests.RequestException as exc:
        log.warning("Could not add OttoMeet tab to chat %s: %s", chat_id, exc)
        return False
