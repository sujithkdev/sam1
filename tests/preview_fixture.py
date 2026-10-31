"""Isolated manual UI smoke-test server. Never starts endpoint collectors."""
import os
import sys
import tempfile
import time
from pathlib import Path
from wsgiref.simple_server import make_server

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="behedr-ui-") as directory:
        os.environ.update(EDR_ENV="development", EDR_JWT_SECRET="isolated-ui-fixture-" + "k" * 64,
                          EDR_BACKGROUND="false", EDR_DATA_DIR=directory)
        from server import create_app
        from server.auth import create_user
        from server.database.storage import _conn, upsert_system, save_alert
        app = create_app()
        create_user("demo", "local-ui-fixture-password", "admin")
        upsert_system({"system_id":"DEMO-WORKSTATION", "hostname":"Isolated UI fixture", "agent_ver":"4.1.0-rc1"})
        save_alert({"system_id":"DEMO-WORKSTATION", "process":"example.exe", "risk_level":"HIGH",
                    "risk_score":80, "reason":"Synthetic UI fixture — no endpoint process was executed."})
        with make_server("127.0.0.1", 0, app) as server:
            server.timeout = 1
            print(f"PREVIEW http://127.0.0.1:{server.server_port}", flush=True)
            deadline = time.monotonic() + 180
            while time.monotonic() < deadline:
                server.handle_request()
        _conn().close()
