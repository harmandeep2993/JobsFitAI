# tests/conftest.py
"""
Shared fixtures for the contract test suite.

The app resolves config.yaml, data/jobsfitai.db, and resumes/ relative to the
working directory. We copy config.yaml into a fresh temp directory and chdir
there BEFORE importing the app, so every test session runs against an empty
database and never touches development data.
"""

import os
import shutil
import sys
import tempfile
import uuid
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

_tmp = tempfile.mkdtemp(prefix="jobfit-test-")
shutil.copy(BACKEND_DIR / "config.yaml", Path(_tmp) / "config.yaml")
os.chdir(_tmp)

import main  # noqa: E402
import api.routes.auth as auth_route  # noqa: E402
import api.routes.resumes as resumes_route  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

# Background extraction after a resume upload calls the real LLM - stub it so
# tests are offline, fast, and free.
resumes_route.extract_resume = lambda text: {"candidate": {"title": "stub"}}

# The developer .env may set INVITE_CODE; disable the gate for the suite.
# test_invite_gate re-enables it explicitly to verify the behaviour.
auth_route._INVITE_CODE = ""


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """The suite makes many calls from one IP/user; clear both limiters per test."""
    auth_route._attempts.clear()
    auth_route._llm_attempts.clear()


@pytest.fixture(scope="session")
def client():
    """TestClient against the app; lifespan (schedulers) intentionally not started."""
    return TestClient(main.app)


@pytest.fixture(scope="session")
def auth(client):
    """Register a throwaway user and return the Authorization header."""
    email = f"test-{uuid.uuid4().hex[:8]}@example.com"
    r = client.post(
        "/api/auth/register", json={"email": email, "password": "testpass123"}
    )
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


RESUME_TEXT = (
    "John Doe\njohn@example.com\nSUMMARY\nData analyst with 3 years experience.\n"
    "WORK EXPERIENCE\nData Analyst at Acme GmbH 2021-2024: built dashboards in "
    "Power BI, SQL queries, Python ETL pipelines.\n"
    "EDUCATION\nBSc Computer Science, TU Berlin, 2020\n"
    "SKILLS\nPython, SQL, Power BI, Excel"
)


@pytest.fixture()
def tmp_token(client, auth):
    """Upload a temp resume and return its opaque token."""
    r = client.post(
        "/api/upload",
        headers=auth,
        files={"file": ("cv.txt", RESUME_TEXT.encode(), "text/plain")},
    )
    assert r.status_code == 200, r.text
    return r.json()["tmp"]
