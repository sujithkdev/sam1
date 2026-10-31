#!/usr/bin/env bash
# Local lab helper. Run with bash linux.sh; never sources .env as shell code.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
umask 077

command_name="${1:-help}"
if [[ $# -gt 0 ]]; then shift; fi
require_env() {
  if [[ ! -x .venv/bin/python ]]; then
    echo 'Run: bash linux.sh setup' >&2
    exit 1
  fi
}
case "$command_name" in
  setup)
    if [[ -x .venv/bin/python ]]; then
      python_bin=.venv/bin/python
    elif command -v python3.12 >/dev/null 2>&1; then
      python_bin=python3.12
    else
      echo 'Python 3.12 with venv support is required. Install it, then retry setup.' >&2
      exit 1
    fi
    "$python_bin" -c 'import sys; assert sys.version_info[:2] == (3,12), "Use Python 3.12 for this locked release"'
    if [[ ! -x .venv/bin/python ]]; then "$python_bin" -m venv .venv; fi
    .venv/bin/python -m pip install -r requirements/server.lock
    .venv/bin/python -m pip check
    if [[ ! -e .env ]]; then
      .venv/bin/python manage.py init
    else
      echo 'Keeping existing .env and runtime data.'
    fi
    mkdir -p var
    echo 'Setup complete. Next: bash linux.sh test'
    ;;
  test)
    require_env
    mkdir -p var
    .venv/bin/python tools/verify_r0_install.py "$PWD"
    echo 'Isolated server smoke test passed. Live Windows delivery is not tested.'
    ;;
  start)
    require_env
    echo 'Lab server: http://127.0.0.1:5000 — keep this terminal open; Ctrl+C stops it.'
    EDR_ENV=development EDR_HOST=127.0.0.1 EDR_PORT=5000 .venv/bin/python manage.py serve
    ;;
  check)
    require_env
    .venv/bin/python - <<'PY'
import sys
from urllib.request import build_opener, ProxyHandler, HTTPRedirectHandler
class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None
opener = build_opener(ProxyHandler({}), NoRedirect())
failed = False
for route in ('health', 'ready'):
    try:
        with opener.open('http://127.0.0.1:5000/' + route, timeout=5) as response:
            status = response.status
            print(f'/{route}: HTTP {status}')
            failed |= status != 200
    except Exception as exc:
        print(f'/{route}: FAILED ({type(exc).__name__})')
        failed = True
sys.exit(1 if failed else 0)
PY
    ;;
  user)
    require_env
    if [[ $# -ne 1 ]]; then echo 'Usage: bash linux.sh user USERNAME' >&2; exit 1; fi
    .venv/bin/python manage.py create-user "$1"
    ;;
  enroll)
    require_env
    if [[ $# -ne 1 ]]; then echo 'Usage: bash linux.sh enroll UNIQUE_HOST_ID' >&2; exit 1; fi
    echo 'This creates an endpoint key; an existing host ID has its key rotated.'
    .venv/bin/python manage.py enroll-agent "$1"
    ;;
  help)
    echo 'Usage: bash linux.sh {setup|test|start|check|user USERNAME|enroll HOST_ID}'
    echo 'setup: install Python dependencies; preserve existing configuration/data'
    echo 'test: isolated server/auth/dashboard smoke test (no live collectors)'
    echo 'start/check: run and verify the loopback-only lab server on port 5000'
    ;;
  *) echo "Unknown command: $command_name" >&2; exit 1 ;;
esac
