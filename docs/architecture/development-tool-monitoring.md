# Development-tool monitoring

This addition observes development-tool process activity. It does **not** grant, revoke or enforce operating-system permissions, and does not prove that a human or AI authored a command. VS Code, Cursor, Windsurf, Codex and Claude executable-name matches are attribution hints, not trusted identities.

The Windows process-polling agent now sends up to eight ancestors, with PID, creation time, executable name and path, plus the child working directory. Ancestor arguments are not collected. Missing permissions, exited parents and depth truncation are represented explicitly. Existing processes present at startup are not newly reported, but their live descendants can include them in ancestry snapshots. Short-lived processes can still be missed. ETW records without this extra context remain unattributed by these new rules.

The server checks the immediate parent identity against the snapshot, stores the source telemetry, and saves an assessment alongside it. The dashboard Evidence button exposes both. Rules flag command-line references to credentials, security changes, persistence, download/execution combinations and elevation. These are intent indicators and can produce false positives. They do not establish that files were read, commands succeeded, traffic was malicious, or a prompt injection occurred. Obfuscation can evade these simple rules.

## Workspace policy

Edit `rules/development_policy.json` on the server and restart it. Only administrators with filesystem access should modify this file. Empty defaults grant no approvals and invent no workspace boundaries.

```json
{
  "workspaces": [
    {"system_id": "YOUR-ENDPOINT-ID", "root": "C:\\work\\your-project"}
  ],
  "approved_operations": []
}
```

An outside-workspace finding concerns **working directory only**, not the destination of a write. Windows paths are normalized lexically with component boundaries; junctions, symlinks and filesystem access need OS-level controls.

An optional reviewed operation must have exactly these keys: `id`, `system_id`, `cwd`, `exe_path`, `sha256`, `cmdline`, `expires_at` (Unix seconds). All string fields must exactly match telemetry, and the approval must not be expired. No wildcard approvals are accepted. Use the actual executable hash from verified evidence. An exact approval suppresses only the new outside-working-directory advisory; it never disables existing malware rules or the new sensitive-behavior rules. Invalid policy prevents server startup.

## Permissions outside this EDR

Run coding tools under a dedicated non-administrator account or disposable VM/container with only the intended workspace mounted. Keep personal credentials and production secrets outside that environment, use narrowly scoped temporary credentials, and require approval for elevation, deployment and destructive operations. This change does not configure your coding tool or machine permissions automatically.

For comprehensive file-read/write and outbound-destination enforcement, use an OS sandbox and validated process-attributed telemetry. The current directory watcher cannot identify who read a credential file, and these changes do not pretend otherwise. Automatic blocking remains disabled pending Windows integration and false-positive testing.
