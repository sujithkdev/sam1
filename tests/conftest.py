import os
import sys
import tempfile
import time
import uuid

import pytest

_temp = tempfile.TemporaryDirectory(prefix="behedr-tests-")
os.environ.update(EDR_ENV="test", EDR_JWT_SECRET="test-only-" + "z" * 64, EDR_BACKGROUND="false",
                  EDR_DATA_DIR=_temp.name, EDR_AGENT_DATA=os.path.join(_temp.name, "agent"))


@pytest.fixture(scope="session")
def app():
    from server import create_app
    application = create_app()
    application.config["TESTING"] = True
    yield application
    from server.database import storage
    connection = getattr(storage._local, "conn", None)
    if connection:
        connection.close()
        storage._local.conn = None
    for connection, _ in storage._connection_pool:
        connection.close()
    storage._connection_pool.clear()
    if "agent" in sys.modules:
        sys.modules["agent"]._spool.conn.close()
    _temp.cleanup()


@pytest.fixture(autouse=True)
def clean_database(app):
    from server.core import temporal
    temporal._windows.clear()
    from server.core import graph, recovery
    graph._graphs.clear()
    recovery.STATE.update(state='ready', rules_hash=recovery.fingerprint())
    from server.database.storage import _conn
    _conn().execute('DELETE FROM recovery_journal')
    _conn().execute('DELETE FROM recovery_checkpoint')
    _conn().execute('DELETE FROM telemetry_tombstones')
    from server.database.storage import _conn
    from server.ratelimit import _buckets
    for table in ("alert_history", "alert_triage", "events", "alerts", "commands", "systems", "users", "agent_credentials", "telemetry", "collector_health", "incidents", "audit_log", "suppressions", "alert_feedback"):
        _conn().execute(f"DELETE FROM {table}")
    _buckets.clear()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def agent_headers():
    from server.auth import enroll_agent
    return {"API-Key": enroll_agent("test-host")}


@pytest.fixture
def event():
    return {"system_id": "test-host", "event": "process_spawn", "parent": "winword.exe", "child": "powershell.exe",
            "pid": 12345, "ppid": 6789, "time": time.time(), "create_time": time.time()-1,
            "event_id": uuid.uuid4().hex, "cmdline": "powershell -enc dGVzdA==", "sha256": "a" * 64,
            "exe_path": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe", "user": "test"}


@pytest.fixture
def admin_headers():
    from server.auth import authenticate, create_user
    create_user("operator", "a-test-password-of-sufficient-length", "admin")
    return {"Authorization": "Bearer " + authenticate("operator", "a-test-password-of-sufficient-length")[1]}
