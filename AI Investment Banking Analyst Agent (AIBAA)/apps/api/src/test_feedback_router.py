"""Tests for the feedback router — thread creation, messaging, role gates."""
import os
import sys

os.environ.setdefault("AIBAA_JWT_SECRET", "test-jwt-secret-for-ci-only")
os.environ.setdefault("AIBAA_DEMO_PASSWORD", "testpass-ci")
os.environ.setdefault("AIBAA_ENVIRONMENT", "development")

from fastapi.testclient import TestClient

sys.path.insert(0, ".")

from dependencies import create_access_token, get_auth_settings, get_demo_users
from main import app


client = TestClient(app)


def _token(role: str) -> str:
    settings = get_auth_settings()
    user = get_demo_users(settings)[role]
    token, _ = create_access_token(
        user_id=user["user_id"],
        tenant_id=user["tenant_id"],
        role=user["role"],
        email=user["email"],
        settings=settings,
    )
    return token


def _headers(role: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token(role)}"}


def test_analyst_can_create_thread_and_post_messages():
    r = client.post(
        "/api/v1/feedback/threads",
        json={"subject": "Dashboard slow", "body": "Loading takes 10s"},
        headers=_headers("analyst"),
    )
    assert r.status_code == 201, r.text
    body = r.json()["data"]
    thread_id = body["thread"]["thread_id"]
    assert body["thread"]["status"] == "open"
    assert body["message"]["author_role"] == "user"

    r2 = client.post(
        f"/api/v1/feedback/threads/{thread_id}/messages",
        json={"body": "Also, export button broken"},
        headers=_headers("analyst"),
    )
    assert r2.status_code == 201, r2.text


def test_analyst_cannot_see_other_users_thread():
    # Admin creates a thread; analyst must not be able to read it.
    create = client.post(
        "/api/v1/feedback/threads",
        json={"subject": "Internal", "body": "Admin-only notes"},
        headers=_headers("admin"),
    )
    thread_id = create.json()["data"]["thread"]["thread_id"]

    r = client.get(
        f"/api/v1/feedback/threads/{thread_id}/messages",
        headers=_headers("analyst"),
    )
    assert r.status_code == 403


def test_admin_sees_all_tenant_threads_and_can_resolve():
    # Analyst creates a thread.
    create = client.post(
        "/api/v1/feedback/threads",
        json={"subject": "Bug report", "body": "Clicking export throws 500"},
        headers=_headers("analyst"),
    )
    assert create.status_code == 201
    thread_id = create.json()["data"]["thread"]["thread_id"]

    # Admin sees it in the list.
    listed = client.get("/api/v1/feedback/threads", headers=_headers("admin"))
    assert listed.status_code == 200
    ids = [t["thread_id"] for t in listed.json()["data"]["threads"]]
    assert thread_id in ids

    # Admin replies, then resolves.
    reply = client.post(
        f"/api/v1/feedback/threads/{thread_id}/messages",
        json={"body": "Thanks — investigating now."},
        headers=_headers("admin"),
    )
    assert reply.status_code == 201
    assert reply.json()["data"]["author_role"] == "admin"

    patch = client.patch(
        f"/api/v1/feedback/threads/{thread_id}",
        json={"status": "resolved"},
        headers=_headers("admin"),
    )
    assert patch.status_code == 200
    assert patch.json()["data"]["status"] == "resolved"


def test_non_admin_cannot_patch_thread_status():
    create = client.post(
        "/api/v1/feedback/threads",
        json={"subject": "test", "body": "msg"},
        headers=_headers("analyst"),
    )
    thread_id = create.json()["data"]["thread"]["thread_id"]

    r = client.patch(
        f"/api/v1/feedback/threads/{thread_id}",
        json={"status": "resolved"},
        headers=_headers("analyst"),
    )
    assert r.status_code == 403


def test_message_body_length_capped():
    create = client.post(
        "/api/v1/feedback/threads",
        json={"subject": "length", "body": "x" * 10},
        headers=_headers("analyst"),
    )
    thread_id = create.json()["data"]["thread"]["thread_id"]

    r = client.post(
        f"/api/v1/feedback/threads/{thread_id}/messages",
        json={"body": "y" * 5000},
        headers=_headers("analyst"),
    )
    assert r.status_code == 422


def test_cannot_post_to_resolved_thread():
    create = client.post(
        "/api/v1/feedback/threads",
        json={"subject": "closing", "body": "initial"},
        headers=_headers("analyst"),
    )
    thread_id = create.json()["data"]["thread"]["thread_id"]

    client.patch(
        f"/api/v1/feedback/threads/{thread_id}",
        json={"status": "resolved"},
        headers=_headers("admin"),
    )

    r = client.post(
        f"/api/v1/feedback/threads/{thread_id}/messages",
        json={"body": "late reply"},
        headers=_headers("analyst"),
    )
    assert r.status_code == 409
