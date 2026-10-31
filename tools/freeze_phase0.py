"""Create or verify the immutable Phase 0 source baseline; never collect secrets/runtime data."""
import argparse
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "phase0"
DIRS = ("backend/server", "endpoint", "rules", "requirements", "tests", "deploy", ".github", "tools")
EXTENSIONS = {".py", ".html", ".css", ".js", ".json", ".yaml", ".yml", ".txt", ".lock", ".md", ".toml"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sources():
    paths = set()
    for directory in DIRS:
        for path in (ROOT / directory).rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts and (
                path.suffix in EXTENSIONS or path.name in {"Dockerfile", "Caddyfile"}
            ):
                paths.add(path)
    paths.update(ROOT.glob("*.md"))
    paths.update(p for p in (ROOT / "docs").rglob("*.md")
                 if p.relative_to(ROOT / "docs").parts[0] not in {"phase0", "phase1", "r0"})
    paths.update(ROOT / name for name in ("manage.py", "pyproject.toml", ".gitignore", ".dockerignore"))
    return sorted(paths)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    manifest = OUT / "baseline-manifest.json"
    archive = OUT / "baseline-source.zip"
    if args.verify:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        if digest(archive.read_bytes()) != data["archive_sha256"]:
            raise SystemExit("Archive checksum mismatch")
        current = {p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in sources()}
        expected = {r["path"]: r["sha256"] for r in data["files"]}
        with zipfile.ZipFile(archive) as z:
            archived = {name: digest(z.read(name)) for name in z.namelist()}
        if archived != expected or current != expected:
            raise SystemExit("Source drift or archive member mismatch")
        print(f"Verified {len(expected)} source files and archive checksum")
        return
    OUT.mkdir(parents=True, exist_ok=True)
    if any((OUT / name).exists() for name in ("baseline-source.zip", "baseline-manifest.json", "environment.json")):
        raise SystemExit("Baseline already exists; refusing to overwrite")
    records = []
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as z:
        for path in sources():
            relative = path.relative_to(ROOT).as_posix()
            content = path.read_bytes()
            z.writestr(relative, content)
            records.append({"path": relative, "bytes": len(content), "sha256": digest(content)})
    manifest.write_text(json.dumps({"schema_version": 1, "snapshot": "phase0-2026-10-22",
        "git_commit": None, "archive_sha256": digest(archive.read_bytes()), "files": records}, indent=2), encoding="utf-8")
    environment = {"python": sys.version, "platform": platform.platform(),
        "packages": sorted([{"name": d.metadata["Name"], "version": d.version}
                            for d in importlib.metadata.distributions()], key=lambda d: d["name"].lower())}
    (OUT / "environment.json").write_text(json.dumps(environment, indent=2), encoding="utf-8")
    print(f"Frozen {len(records)} source files; SHA-256 {digest(archive.read_bytes())}")


if __name__ == "__main__":
    main()
