"""Entry point for the "Consent geben" / "Consent ablehnen" buttons of the OttoMeet Teams side panel.

Add this route to backend/app/routers/teams_router/teams_consent_routes.py.

Flow:
    Teams app  ->  GET /teams/consent-entry?chat_id=<meeting chat id>&act=accept|decline
               ->  302 /teams/consent?token=…  or  /teams/withdraw_consent?token=…   (existing flow)
               ->  Entra sign-in, confirmation page, consents row, chat notice, permission sync

The link only identifies the meeting and the action; the consenting identity still comes from
the Entra sign-in on /teams/consent, exactly as with the privacy card in the chat.

Adapt the two marked calls to the existing helpers:
    - find_open_session_by_chat_id  -> query consent_sessions WHERE chat_id = :chat_id AND closed = false,
                                       newest created_at first
    - build_consent_token           -> the same function that builds the privacy card links {sid, act, jti, exp}
"""
from html import escape
from typing import Literal

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse, RedirectResponse

from app.db.repositories import consent_repository  # adapt import path
from app.routers.teams_router.teams_router_helper_functions import build_consent_token  # adapt name

router = APIRouter()

TARGETS = {
    "accept": "/teams/consent",
    "decline": "/teams/withdraw_consent",
}


def _info_page(title: str, text: str, status: int) -> HTMLResponse:
    body = f"""<!doctype html><html lang="de"><meta charset="utf-8">
<title>{escape(title)}</title>
<body style="font-family:Segoe UI,Arial,sans-serif;max-width:640px;margin:48px auto;padding:0 16px">
<h1>{escape(title)}</h1><p>{escape(text)}</p></body></html>"""
    return HTMLResponse(body, status_code=status)


@router.get("/teams/consent-entry")
def consent_entry(
    chat_id: str = Query(..., min_length=5, max_length=512),
    act: Literal["accept", "decline"] = Query("accept"),
):
    session = consent_repository.find_open_session_by_chat_id(chat_id)  # adapt
    if session is None:
        return _info_page(
            "OttoMeet ist nicht aktiv",
            "In dieser Besprechung läuft gerade keine OttoMeet-Transkription. "
            "Eine Einwilligung ist erst möglich, wenn OttoMeet gestartet wurde.",
            404,
        )

    token = build_consent_token(session_id=session.session_id, act=act)  # adapt
    return RedirectResponse(f"{TARGETS[act]}?token={token}", status_code=302)
