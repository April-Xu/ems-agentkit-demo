"""Synthetic EMS MCP/governance backend for the public AgentKit demo.

This service deliberately uses bundled synthetic records and mock downstream
adapters by default. It is not the customer's production governance service.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
import hashlib
import json
import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx
import uvicorn
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route


MODULE_DIR = Path(__file__).resolve().parent
try:
    ROOT = MODULE_DIR.parents[1]
except IndexError:
    ROOT = MODULE_DIR
FIXTURE_DIR = Path(os.getenv("EMS_FIXTURE_DIR", ROOT / "data" / "feishu"))
STATE_DB = Path(os.getenv("EMS_DEMO_STATE_DB", "/tmp/ems-agentkit-demo.sqlite3"))
MAX_GRANT_MINUTES = 15
MAX_BATCH_SIZE = 3
DEMO_EVENT_ID = "DEMO-IW-2026-001"


def transport_security() -> TransportSecuritySettings | None:
    """Keep DNS-rebinding protection enabled for the public MCP gateway."""
    allowed_hosts = [
        host.strip()
        for host in os.getenv("EMS_MCP_ALLOWED_HOSTS", "").split(",")
        if host.strip()
    ]
    allowed_origins = [
        origin.strip()
        for origin in os.getenv("EMS_MCP_ALLOWED_ORIGINS", "").split(",")
        if origin.strip()
    ]
    if not allowed_hosts and not allowed_origins:
        # Preserve FastMCP's localhost defaults for local development.
        return None
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=allowed_hosts,
        allowed_origins=allowed_origins,
    )


mcp = FastMCP(
    "ems-impact-week-demo",
    transport_security=transport_security(),
)


def now() -> datetime:
    return datetime.now(timezone.utc)


def timestamp(value: datetime | None = None) -> str:
    return (value or now()).isoformat(timespec="seconds")


def read_fixture(name: str) -> list[dict[str, Any]]:
    path = FIXTURE_DIR / name
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload["create_records"]


def canonical_hash(value: Any) -> str:
    body = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def change_set_payload(change_set: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "changeSetId", "version", "eventId", "batchId", "sessionId", "sessionName",
        "participantIds", "participants", "reason", "sourceVersion", "policyVersion",
        "grantId",
    )
    return {key: change_set[key] for key in fields}


def init_db() -> None:
    STATE_DB.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(STATE_DB) as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS objects (kind TEXT, id TEXT, json TEXT, "
            "PRIMARY KEY(kind, id))"
        )
        db.execute(
            "CREATE TABLE IF NOT EXISTS idempotency (key TEXT PRIMARY KEY, job_id TEXT)"
        )


def save(kind: str, object_id: str, value: dict[str, Any]) -> None:
    with sqlite3.connect(STATE_DB) as db:
        db.execute(
            "INSERT INTO objects(kind, id, json) VALUES(?, ?, ?) "
            "ON CONFLICT(kind, id) DO UPDATE SET json=excluded.json",
            (kind, object_id, json.dumps(value, ensure_ascii=False)),
        )


def load(kind: str, object_id: str) -> dict[str, Any] | None:
    with sqlite3.connect(STATE_DB) as db:
        row = db.execute(
            "SELECT json FROM objects WHERE kind=? AND id=?", (kind, object_id)
        ).fetchone()
    return json.loads(row[0]) if row else None


def list_saved(kind: str, status: str | None = None) -> list[dict[str, Any]]:
    with sqlite3.connect(STATE_DB) as db:
        rows = db.execute("SELECT json FROM objects WHERE kind=? ORDER BY id", (kind,))
        values = [json.loads(row[0]) for row in rows]
    return [value for value in values if status is None or value.get("status") == status]


def event_record(event_id: str) -> dict[str, Any]:
    for event in read_fixture("events.batch.json"):
        if event["活动编号"] == event_id:
            return event
    raise ValueError(f"Unknown demo event: {event_id}")


def session_record(session_id: str) -> dict[str, Any]:
    for session in read_fixture("sessions.batch.json"):
        if session["排期编号"] == session_id:
            return session
    raise ValueError(f"Unknown demo session: {session_id}")


@mcp.tool()
def list_events() -> list[dict[str, Any]]:
    """Read synthetic EMS events loaded from the demo Feishu Base export."""
    return read_fixture("events.batch.json")


@mcp.tool()
def list_sessions(event_id: str) -> list[dict[str, Any]]:
    """Read sessions for one event. This demo service has no Base write tool."""
    event_record(event_id)
    return [
        row for row in read_fixture("sessions.batch.json")
        if row.get("活动编号") == event_id
    ]


@mcp.tool()
def list_participants(event_id: str) -> list[dict[str, Any]]:
    """Read synthetic participant rows associated with the demo event."""
    event_record(event_id)
    return read_fixture("participants.batch.json")


@mcp.tool()
def list_enrollment_requests(batch_id: str) -> list[dict[str, Any]]:
    """Read requests from the synthetic Feishu Base export."""
    return [
        row for row in read_fixture("enrollment-requests.batch.json")
        if row.get("批次编号") == batch_id
    ]


@mcp.tool()
def simplybook_list_calendars(event_id: str) -> list[dict[str, Any]]:
    """MCP wrapper for the SimplyBook calendar read contract; mock by default."""
    event_record(event_id)
    if os.getenv("EMS_SIMPLYBOOK_MODE", "mock") != "live":
        return [
            {
                "calendarId": row["SimplyBook排期ID"],
                "demoSessionId": row["排期编号"],
                "name": row["课程名称"],
                "startsAt": row["开始时间"],
                "endsAt": row["结束时间"],
                "remaining": row["剩余名额"],
                "source": "synthetic fixture; not a live SimplyBook response",
            }
            for row in read_fixture("sessions.batch.json")
            if row.get("活动编号") == event_id
        ]

    return _simplybook_get("/calendars")


@mcp.tool()
def simplybook_list_bookings(calendar_id: str) -> list[dict[str, Any]]:
    """MCP wrapper for GET /calendars/{calendarId}/bookings; read-only."""
    if os.getenv("EMS_SIMPLYBOOK_MODE", "mock") != "live":
        return [
            row for row in read_fixture("current-bookings.batch.json")
            if next(
                (s["SimplyBook排期ID"] for s in read_fixture("sessions.batch.json")
                 if s["排期编号"] == row["排期编号"]),
                None,
            ) == calendar_id
        ]
    return _simplybook_get(f"/calendars/{calendar_id}/bookings")


def _simplybook_get(path: str) -> Any:
    base_url = os.getenv("SIMPLY_BOOK_API_BASE_URL", "").rstrip("/")
    token = os.getenv("SIMPLY_BOOK_JWT", "")
    app_id = os.getenv("SIMPLY_BOOK_APP_ID", "")
    platform = os.getenv("SIMPLY_BOOK_PLATFORM", "")
    if not all((base_url, token, app_id, platform)):
        raise ValueError(
            "Live SimplyBook mode requires SIMPLY_BOOK_API_BASE_URL, "
            "SIMPLY_BOOK_JWT, SIMPLY_BOOK_APP_ID, and SIMPLY_BOOK_PLATFORM"
        )
    response = httpx.get(
        f"{base_url}{path}",
        headers={
            "Token": token,
            "Appid": app_id,
            "Platform": platform,
            "Lang": "en",
        },
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


@mcp.tool()
def request_temporary_grant(
    event_id: str,
    batch_id: str,
    actions: list[str],
    purpose: str,
    duration_minutes: int = 15,
) -> dict[str, Any]:
    """Request a short-lived, event-scoped demo Grant; approval is separate."""
    event_record(event_id)
    if event_id != DEMO_EVENT_ID:
        raise ValueError("The public demo is restricted to its synthetic event")
    if duration_minutes < 1 or duration_minutes > MAX_GRANT_MINUTES:
        raise ValueError(f"Demo Grant duration must be 1-{MAX_GRANT_MINUTES} minutes")
    allowed = {
        "read", "prepare_enrollment", "freeze_changeset", "submit_approval",
        "execute_approved_changeset",
    }
    if not actions or set(actions) - allowed:
        raise ValueError(f"Requested actions must be a subset of {sorted(allowed)}")
    grant_id = f"GRANT-DEMO-{secrets.token_hex(4).upper()}"
    grant = {
        "grantId": grant_id,
        "subject": os.getenv("EMS_DEMO_OPERATOR_SUBJECT", "demo.operator"),
        "eventId": event_id,
        "batchId": batch_id,
        "actions": sorted(set(actions)),
        "maxItems": MAX_BATCH_SIZE,
        "durationMinutes": duration_minutes,
        "status": "PENDING_APPROVAL",
        "requestedAt": timestamp(),
        "expiresAt": None,
        "approvalMode": "manual demo reviewer endpoint; not Feishu",
        "purpose": purpose[:500],
    }
    save("grant", grant_id, grant)
    return grant


@mcp.tool()
def get_grant(grant_id: str) -> dict[str, Any]:
    """Read the status and scope of a demo Grant."""
    grant = load("grant", grant_id)
    if not grant:
        raise ValueError("Grant not found")
    return grant


@mcp.tool()
def prepare_change_set(
    grant_id: str,
    event_id: str,
    batch_id: str,
    session_id: str,
    participant_ids: list[str],
    reason: str,
) -> dict[str, Any]:
    """Prepare a bounded enrollment preview; this performs no business writes."""
    grant = load("grant", grant_id)
    if not grant or grant.get("status") != "ACTIVE":
        raise ValueError("An ACTIVE demo Grant is required before preparation")
    if grant["eventId"] != event_id or grant["batchId"] != batch_id:
        raise ValueError("Grant does not cover this event and batch")
    if "prepare_enrollment" not in grant["actions"]:
        raise ValueError("Grant does not allow enrollment preparation")
    if datetime.fromisoformat(grant["expiresAt"]) <= now():
        raise ValueError("Grant expired; request a new Grant")
    session = session_record(session_id)
    if session.get("活动编号") != event_id:
        raise ValueError("Session is outside the granted event")
    if len(participant_ids) > min(MAX_BATCH_SIZE, int(grant["maxItems"])):
        raise ValueError(f"Demo policy allows at most {MAX_BATCH_SIZE} rows")
    participants = {p["人员编号"]: p for p in read_fixture("participants.batch.json")}
    if len(participant_ids) != len(set(participant_ids)):
        raise ValueError("Duplicate participant IDs are not allowed")
    unknown = sorted(set(participant_ids) - participants.keys())
    if unknown:
        raise ValueError(f"Unknown demo participant IDs: {unknown}")
    selected = [participants[pid] for pid in participant_ids]
    without_consent = [p["人员编号"] for p in selected if not p.get("报名同意")]
    if without_consent:
        raise ValueError(f"Consent is missing for participant IDs: {without_consent}")
    email_owners: dict[str, list[str]] = {}
    for person in participants.values():
        email_owners.setdefault(person["邮箱"].strip().casefold(), []).append(person["人员编号"])
    ambiguous = [
        p["人员编号"] for p in selected
        if len(email_owners.get(p["邮箱"].strip().casefold(), [])) > 1
    ]
    if ambiguous:
        raise ValueError(f"Duplicate-email candidates require human resolution: {ambiguous}")
    current_bookings = read_fixture("current-bookings.batch.json")
    existing = [
        p["人员编号"] for p in selected
        if any(b.get("人员编号") == p["人员编号"] for b in current_bookings)
    ]
    if existing:
        raise ValueError(f"Already-enrolled participant IDs: {existing}")
    sessions_by_id = {
        row["排期编号"]: row for row in read_fixture("sessions.batch.json")
    }
    target_start = datetime.strptime(session["开始时间"], "%Y-%m-%d %H:%M")
    target_end = datetime.strptime(session["结束时间"], "%Y-%m-%d %H:%M")
    conflicts: list[str] = []
    for person in selected:
        for booking in current_bookings:
            if booking.get("人员编号") != person["人员编号"]:
                continue
            booked_session = sessions_by_id.get(booking.get("排期编号"))
            if not booked_session:
                continue
            booked_start = datetime.strptime(booked_session["开始时间"], "%Y-%m-%d %H:%M")
            booked_end = datetime.strptime(booked_session["结束时间"], "%Y-%m-%d %H:%M")
            if target_start < booked_end and booked_start < target_end:
                conflicts.append(person["人员编号"])
    if conflicts:
        raise ValueError(f"Overlapping existing booking for participant IDs: {sorted(set(conflicts))}")
    if len(participant_ids) > int(session["剩余名额"]):
        raise ValueError("Requested enrollment exceeds remaining session capacity")
    booking = {
        "changeSetId": f"CS-DEMO-{secrets.token_hex(4).upper()}",
        "version": 1,
        "eventId": event_id,
        "batchId": batch_id,
        "sessionId": session_id,
        "sessionName": session["课程名称"],
        "participantIds": sorted(participant_ids),
        "participants": [
            {"participantId": pid, "name": participants[pid]["姓名"]}
            for pid in sorted(participant_ids)
        ],
        "reason": reason[:500],
        "sourceVersion": "synthetic-feishu-fixtures-v1",
        "policyVersion": "demo-policy-v1",
        "status": "PREPARED",
        "preparedAt": timestamp(),
        "grantId": grant_id,
        "payloadHash": None,
        "approvalInstanceId": None,
    }
    booking["payloadHash"] = canonical_hash(change_set_payload(booking))
    save("changeset", booking["changeSetId"], booking)
    return booking


@mcp.tool()
def get_change_set(change_set_id: str) -> dict[str, Any]:
    """Read a preview, status, version, and immutable payload hash."""
    change_set = load("changeset", change_set_id)
    if not change_set:
        raise ValueError("Change Set not found")
    return change_set


@mcp.tool()
def freeze_change_set(
    change_set_id: str, expected_version: int, expected_hash: str
) -> dict[str, Any]:
    """Freeze an exact preview version and hash; freezing does not execute it."""
    change_set = load("changeset", change_set_id)
    if not change_set:
        raise ValueError("Change Set not found")
    if change_set["status"] != "PREPARED":
        raise ValueError("Only a PREPARED Change Set can be frozen")
    if change_set["version"] != expected_version or not secrets.compare_digest(
        change_set["payloadHash"], expected_hash
    ):
        raise ValueError("Version/hash mismatch; prepare and review a new Change Set")
    grant = load("grant", change_set["grantId"])
    if not grant or grant["status"] != "ACTIVE" or datetime.fromisoformat(grant["expiresAt"]) <= now():
        raise ValueError("Grant is not active; request a new Grant")
    if "freeze_changeset" not in grant["actions"]:
        raise ValueError("Grant does not allow freezing a Change Set")
    change_set["status"] = "FROZEN"
    change_set["frozenAt"] = timestamp()
    save("changeset", change_set_id, change_set)
    return change_set


@mcp.tool()
def submit_change_set_approval(
    change_set_id: str, expected_version: int, expected_hash: str, comment: str = ""
) -> dict[str, Any]:
    """Submit a frozen demo Change Set for a separate human review."""
    change_set = load("changeset", change_set_id)
    if not change_set or change_set["status"] != "FROZEN":
        raise ValueError("Only a frozen Change Set can be submitted")
    if change_set["version"] != expected_version or not secrets.compare_digest(
        change_set["payloadHash"], expected_hash
    ):
        raise ValueError("Version/hash mismatch; approval was not created")
    grant = load("grant", change_set["grantId"])
    if not grant or grant["status"] != "ACTIVE" or "submit_approval" not in grant["actions"]:
        raise ValueError("An active Grant with approval-submission scope is required")
    if datetime.fromisoformat(grant["expiresAt"]) <= now():
        raise ValueError("Grant expired; request a new Grant")
    approval_id = f"MOCK-APPROVAL-{secrets.token_hex(4).upper()}"
    change_set["status"] = "PENDING_APPROVAL"
    change_set["approvalInstanceId"] = approval_id
    change_set["approvalComment"] = comment[:500]
    save("changeset", change_set_id, change_set)
    return {
        "changeSetId": change_set_id,
        "approvalInstanceId": approval_id,
        "status": "PENDING",
        "approvalUrl": "MOCK ONLY: use the private demo reviewer endpoint; not a Feishu URL",
    }


async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "ems-demo-mcp", "mode": "synthetic"})


def require_secret(request: Request, env_name: str) -> bool:
    expected = os.getenv(env_name, "")
    supplied = request.headers.get("authorization", "")
    return bool(expected) and secrets.compare_digest(supplied, f"Bearer {expected}")


async def reviewer_queue(request: Request) -> JSONResponse:
    if not (
        require_secret(request, "EMS_DEMO_GRANT_REVIEWER_KEY")
        or require_secret(request, "EMS_DEMO_CHANGESET_REVIEWER_KEY")
    ):
        return JSONResponse({"error": "reviewer authorization required"}, status_code=401)
    return JSONResponse({
        "pendingGrants": list_saved("grant", "PENDING_APPROVAL"),
        "pendingChangeSets": list_saved("changeset", "PENDING_APPROVAL"),
        "demoOnly": True,
    })


async def approve_grant(request: Request) -> JSONResponse:
    if not require_secret(request, "EMS_DEMO_GRANT_REVIEWER_KEY"):
        return JSONResponse({"error": "reviewer authorization required"}, status_code=401)
    grant_id = request.path_params["grant_id"]
    grant = load("grant", grant_id)
    if not grant or grant["status"] != "PENDING_APPROVAL":
        return JSONResponse({"error": "pending Grant not found"}, status_code=404)
    expiry = now() + timedelta(minutes=int(grant["durationMinutes"]))
    grant.update({"status": "ACTIVE", "approvedAt": timestamp(), "expiresAt": timestamp(expiry),
                  "approvedBy": "synthetic.demo.grant-reviewer"})
    save("grant", grant_id, grant)
    return JSONResponse(grant)


async def approve_change_set(request: Request) -> JSONResponse:
    if not require_secret(request, "EMS_DEMO_CHANGESET_REVIEWER_KEY"):
        return JSONResponse({"error": "reviewer authorization required"}, status_code=401)
    change_set_id = request.path_params["change_set_id"]
    change_set = load("changeset", change_set_id)
    if not change_set or change_set["status"] != "PENDING_APPROVAL":
        return JSONResponse({"error": "pending Change Set not found"}, status_code=404)
    current_hash = canonical_hash(change_set_payload(change_set))
    if not secrets.compare_digest(current_hash, change_set["payloadHash"]):
        return JSONResponse({"error": "frozen payload hash mismatch"}, status_code=409)
    grant = load("grant", change_set["grantId"])
    grant_reviewer = grant.get("approvedBy") if grant else None
    change_set_reviewer = "synthetic.demo.changeset-reviewer"
    if grant_reviewer == change_set_reviewer:
        return JSONResponse({"error": "Grant and Change Set reviewers must be different"}, status_code=409)
    change_set.update({"status": "APPROVED", "reviewedAt": timestamp(),
                       "reviewedBy": change_set_reviewer})
    save("changeset", change_set_id, change_set)
    return JSONResponse(change_set)


async def execute_mock(request: Request) -> JSONResponse:
    if not require_secret(request, "EMS_DEMO_WORKER_KEY"):
        return JSONResponse({"error": "worker authorization required"}, status_code=401)
    change_set_id = request.path_params["change_set_id"]
    change_set = load("changeset", change_set_id)
    if not change_set:
        return JSONResponse({"error": "Change Set not found"}, status_code=404)
    try:
        body = await request.json()
    except Exception:
        body = {}
    if body.get("expectedVersion") != change_set["version"] or body.get("expectedHash") != change_set["payloadHash"]:
        return JSONResponse({"error": "Change Set hash mismatch"}, status_code=409)
    idem_key = request.headers.get("idempotency-key", "")
    if len(idem_key) < 16:
        return JSONResponse({"error": "Idempotency-Key must be at least 16 characters"}, status_code=400)
    grant = load("grant", change_set["grantId"])
    if not grant or grant["status"] != "ACTIVE" or datetime.fromisoformat(grant["expiresAt"]) <= now():
        return JSONResponse({"error": "Grant expired or revoked"}, status_code=409)
    if "execute_approved_changeset" not in grant["actions"]:
        return JSONResponse({"error": "Grant does not authorize Worker execution"}, status_code=403)
    with sqlite3.connect(STATE_DB) as db:
        previous = db.execute("SELECT job_id FROM idempotency WHERE key=?", (idem_key,)).fetchone()
        if previous:
            existing = load("job", previous[0])
            if existing and existing.get("changeSetId") != change_set_id:
                return JSONResponse({"error": "Idempotency-Key was used for another Change Set"}, status_code=409)
            return JSONResponse(existing or {"jobId": previous[0], "status": "DUPLICATE"})
        if change_set["status"] != "APPROVED":
            return JSONResponse({"error": "Change Set is not finally approved"}, status_code=409)
        job_id = f"JOB-DEMO-{secrets.token_hex(4).upper()}"
        job = {
            "jobId": job_id,
            "changeSetId": change_set_id,
            "status": "SIMULATED",
            "simplyBook": {"status": "MOCK_ONLY_NOT_SENT", "bookingIds": []},
            "impactKey": {"status": "MOCK_ONLY_NOT_SYNCED", "externalReference": None},
            "message": "No write was sent to SimplyBook or Impact Key.",
            "createdAt": timestamp(),
        }
        db.execute("INSERT INTO idempotency(key, job_id) VALUES(?, ?)", (idem_key, job_id))
    save("job", job_id, job)
    change_set["status"] = "SIMULATED"
    change_set["jobId"] = job_id
    save("changeset", change_set_id, change_set)
    return JSONResponse(job, status_code=202)


async def get_job(request: Request) -> JSONResponse:
    if not require_secret(request, "EMS_DEMO_WORKER_KEY"):
        return JSONResponse({"error": "worker authorization required"}, status_code=401)
    job = load("job", request.path_params["job_id"])
    return JSONResponse(job or {"error": "job not found"}, status_code=200 if job else 404)


routes = [
    Route("/health", health, methods=["GET"]),
    Route("/demo/reviewer/queue", reviewer_queue, methods=["GET"]),
    Route("/demo/reviewer/grants/{grant_id}/approve", approve_grant, methods=["POST"]),
    Route("/demo/reviewer/change-sets/{change_set_id}/approve", approve_change_set, methods=["POST"]),
    Route("/internal/change-sets/{change_set_id}/execute", execute_mock, methods=["POST"]),
    Route("/internal/jobs/{job_id}", get_job, methods=["GET"]),
    Mount("/", app=mcp.streamable_http_app()),
]


@asynccontextmanager
async def lifespan(_: Starlette):
    init_db()
    async with mcp.session_manager.run():
        yield


app = Starlette(routes=routes, lifespan=lifespan)


if __name__ == "__main__":
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
