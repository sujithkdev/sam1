# Linux quick start

For Kali/Linux lab use. Python 3.12 with venv support and Git are prerequisites.
This helper does not install system packages, enable services or expose HTTP to
the network. Keep the Windows agent in its Windows VM.

## Download

sam1 is private: sign in with a GitHub account that can access it. With GitHub CLI:

```bash
gh auth login
gh repo clone sujithkdev/sam1
cd sam1
```

Alternatively use GitHub's Download ZIP while signed in, extract it, and open a
terminal in the extracted folder containing linux.sh. Never put a GitHub token
in a clone URL or paste it into this chat.

## Install and test

```bash
bash linux.sh setup
bash linux.sh test
```

Setup creates .venv and a random .env secret only when needed. Existing .env,
credentials and databases are preserved. Missing Python 3.12 or unavailable
locked dependencies are reported as failures; setup does not substitute versions.
The test uses temporary state and checks server creation, authentication,
dashboard APIs, assets and logout. It does not run malware or Windows collectors.

For a new installation only, create your administrator:

```bash
bash linux.sh user admin
```

Choose a password of at least 14 characters. Existing installations should reuse
their account. The helper uses the existing configured data directory.

## Run

```bash
bash linux.sh start
```

Keep that terminal open. In another terminal, from the same folder:

```bash
bash linux.sh check
```

Both routes should show HTTP 200. Open http://127.0.0.1:5000 on Kali and log in.
This explicitly starts a development lab listener bound to loopback port 5000,
not a public HTTPS production service. Do not run a second server against the
same database if one is already running.

## Connect the Windows guest

Use the existing SSH tunnel, agent identity and credential. If this is a new
endpoint only, issue a key with `bash linux.sh enroll win10-lab`; repeating that
command rotates that host's key. Keep the printed key private.

Windows PowerShell (replace placeholders; leave this window open):

```powershell
ssh -N -o ExitOnForwardFailure=yes -L 127.0.0.1:5000:127.0.0.1:5000 KALI_USERNAME@KALI_IP
```

Verify the first-connection fingerprint. Use the Windows agent's documented
configuration and entry point from the project README. A health check alone
does not prove authenticated ingestion or detection.

## Share results

Send setup/test errors and the output of `bash linux.sh check`, with secrets
removed. For queue/delivery diagnosis follow [the verification workflow](verification-workflow.md).
Continue with [P1](../development/P1_LIVE_TRANSPORT_2026-10-30.md) and
[P2](../development/P2_WINDOWS_TELEMETRY_2026-10-30.md); neither is completed by
this local server smoke test.
