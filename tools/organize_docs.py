"""One-time documentation migration with a relocation record and link rewriting."""
import json
import os
from pathlib import Path
import re
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
GROUPS = {
    'publication': ['IEEE_PUBLICATION_AND_MALWARE_EVALUATION_PLAN.md'],
    'development': ['P1_LIVE_TRANSPORT_2026-10-30.md', 'P2_WINDOWS_TELEMETRY_2026-10-30.md'],
    'architecture': ['implementation.md', 'development-tool-monitoring.md',
                     'dashboard-redesign.md', 'phase3-sysmon.md', 'phase4-correlation.md',
                     'phase5-recovery.md', 'phase6-rules.md', 'reference-integration-2026-10-22.md'],
    'operations': ['operations.md', 'migration.md', 'phase2-deployment.md',
                   'phase8-operations.md', 'verification-workflow.md', 'sender-fix-2026-10-25.md'],
    'evaluation': ['phase7-evaluation.md', 'phase9-dataset-evaluation.md'],
    'evidence': ['verification.md', 'verification-2026-10-25.md',
                 'phase2-verification-2026-10-22.md', 'phase8-verification-2026-10-23.md',
                 'phase1-security-2026-10-22.md', 'phase6-closeout.md',
                 'CLEANUP_2026-10-30.md', 'cleanup-2026-10-30.json', 'dependency-audit.json'],
    'history': ['evaluation-2026-10-16.md', 'phase-1-research-2026-10-16.md'],
}
ROOT_HISTORY = ['CURRENT_CODEBASE_ANALYSIS.md', 'PROJECT_IMPLEMENTATION_REPORT.md',
                'PROJECT_MASTER_PLAN.md', 'RESEARCH_DOSSIER.md']


def main():
    mapping = {ROOT/'docs'/name: ROOT/'docs'/group/name
               for group, names in GROUPS.items() for name in names}
    mapping.update({ROOT/name: ROOT/'docs/history'/name for name in ROOT_HISTORY})
    record = ROOT/'docs/relocation-2026-10-30.json'
    if record.exists():
        raise SystemExit('Migration already recorded; refusing to repeat')
    for old, new in mapping.items():
        if not old.is_file() or new.exists():
            raise ValueError(f'Missing source or existing destination: {old}')
        for path in (old, new):
            if not path.resolve().is_relative_to(ROOT):
                raise ValueError('Path escapes project')
    documents = [ROOT/'README.md', *ROOT.glob('*.md'), *(ROOT/'docs').rglob('*.md')]
    documents = list(dict.fromkeys(documents))
    originals = {path: path.read_text(encoding='utf-8-sig') for path in documents}
    # Persist the mapping before moves, making interrupted runs reviewable.
    record.write_text(json.dumps({str(a.relative_to(ROOT).as_posix()): b.relative_to(ROOT).as_posix()
                                 for a, b in mapping.items()}, indent=2)+'\n', encoding='utf-8')
    for old, new in mapping.items():
        new.parent.mkdir(parents=True, exist_ok=True)
        old.rename(new)
    for old, content in originals.items():
        new = mapping.get(old, old)

        def rewrite(match):
            target = match.group(1)
            if re.match(r'^[a-zA-Z][\w+.-]*:', target) or target.startswith(('#', '/')):
                return match.group(0)
            raw, sep, fragment = target.partition('#')
            resolved = (old.parent/unquote(raw)).resolve()
            destination = mapping.get(resolved, resolved)
            if not resolved.is_relative_to(ROOT):
                return match.group(0)
            updated = Path(os.path.relpath(destination, new.parent)).as_posix()
            return '](' + updated + (sep+fragment if sep else '') + ')'

        content = re.sub(r'\]\(([^\s()]+)\)', rewrite, content)
        # Update explicit project-root references in prose/code as well as links.
        for source, destination in sorted(mapping.items(), key=lambda pair: -len(str(pair[0]))):
            before = source.relative_to(ROOT).as_posix()
            after = destination.relative_to(ROOT).as_posix()
            content = content.replace('`'+before+'`', '`'+after+'`')
        if content != originals[old]:
            new.write_text(content, encoding='utf-8')
    # Package source selection and generated README paths must follow the new tree.
    builder = ROOT/'tools/build_packages.py'
    content = builder.read_text(encoding='utf-8')
    for old, new in mapping.items():
        content = content.replace(old.relative_to(ROOT).as_posix(), new.relative_to(ROOT).as_posix())
    builder.write_text(content, encoding='utf-8')
    print(f'Moved {len(mapping)} documents/sidecars; updated project Markdown links and package paths.')


if __name__ == '__main__':
    main()
