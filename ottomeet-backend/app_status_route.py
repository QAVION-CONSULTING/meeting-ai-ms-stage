"""Status endpoint for the OttoMeet Teams side panel.

Add this route to backend/app/routers/teams_router/teams_consent_routes.py (or a new router).

The side panel polls
    GET /teams/app-status?chat_id=<meeting chat id>&user_oid=<Entra object id>&upn=<UPN>
every few seconds and renders "Consent erforderlich" / "Consent erteilt" / "Consent abgelehnt".

The eligibility rules mirror section 9 of the consent documentation:
    decline in this session  -> not consented (overrides everything)
    tagged mode              -> consented
    latest decision accept   -> consented
    active persistent consent -> consented
    otherwise                -> not consented

Adapt the three marked calls to the existing repositories.

CORS: the side panel runs on https://qavion-consulting.github.io and calls this route with fetch(),
so the FastAPI app needs
    app.add_middleware(CORSMiddleware, allow_origins=["https://qavion-consulting.github.io"],
                       allow_methods=["GET"], allow_headers=["Accept"])
"""
from typing import Optional

from fastapi import APIRouter, Query

from app.db.repositories import consent_repository, user_repository  # adapt import path

router = APIRouter()


@router.get("/teams/app-status")
def app_status(
    chat_id: str = Query(..., min_length=5, max_length=512),
    user_oid: str = Query("", max_length=64),
    upn: str = Query("", max_length=320),
):
    session = consent_repository.find_open_session_by_chat_id(chat_id)  # adapt
    if session is None:
        return {"session_active": False}

    decision: Optional[str] = None
    if user_oid:
        # latest consents row for (session_id, user_oid) -> "accept" | "decline" | None
        decision = consent_repository.latest_decision(session.session_id, user_oid)  # adapt

    persistent = bool(upn) and user_repository.has_active_persistent_consent(upn)  # adapt (latest row by UPN, case-insensitive)

    if decision == "decline":
        consented = False
    elif session.recording_mode == "tagged":
        consented = True
    elif decision == "accept":
        consented = True
    else:
        consented = persistent

    return {
        "session_active": True,
        "recording_mode": session.recording_mode,
        "decision": decision or "none",
        "persistent_consent": persistent,
        "consented": consented,
        "started_at": session.created_at.isoformat() if session.created_at else None,
    }
