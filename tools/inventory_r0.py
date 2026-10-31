"""Read-only source/baseline inventory; writes a new report without secrets."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = ('backend/server', 'endpoint', 'rules', 'requirements', 'tests', 'deploy', 'tools', '.github')
EXTENSIONS = {'.py', '.html', '.css', '.js', '.cjs', '.json', '.yaml', '.yml', '.txt', '.lock', '.md', '.toml', '.xml', '.ps1', '.sh'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def inventory(root=ROOT):
    files = set()
    for directory in DIRECTORIES:
        for p in (root/directory).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and (p.suffix in EXTENSIONS or p.name in {'LICENSE', 'Dockerfile', 'Caddyfile'}):
                if p.is_symlink() or not p.resolve().is_relative_to(root.resolve()):
                    raise ValueError('Source link outside inventory policy')
                files.add(p)
    files.update(p for p in (root/'docs').rglob('*.md')
                 if p.relative_to(root/'docs').parts[0] not in {'r0', 'phase0', 'phase1'})
    files.update(p for p in root.glob('*.md'))
    files.update(root/n for n in ('manage.py', 'pyproject.toml', '.gitignore', '.dockerignore'))
    sources = {p.relative_to(root).as_posix(): sha(p.read_bytes()) for p in sorted(files) if p.is_file()}
    baselines = {}
    for name in ('phase0', 'phase1'):
        folder = root/'docs'/name
        manifest = json.loads((folder/'baseline-manifest.json').read_text(encoding='utf-8'))
        archive = folder/'baseline-source.zip'
        expected = {r['path']: r['sha256'] for r in manifest['files']}
        with zipfile.ZipFile(archive) as z:
            members = {n: sha(z.read(n)) for n in z.namelist()}
        baselines[name] = {'archive_sha256': sha(archive.read_bytes()),
                           'manifest_sha256': sha((folder/'baseline-manifest.json').read_bytes()),
                           'archive_matches': sha(archive.read_bytes()) == manifest['archive_sha256'],
                           'members_match': members == expected}
    packages = {}
    for folder in sorted((root/'dist').glob('*')):
        for name in ('server', 'agent'):
            manifest_path = folder/name/'MANIFEST.json'
            if not manifest_path.is_file():
                continue
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
            changed = []
            for path, digest in manifest['files'].items():
                target = folder/name/path
                if not target.resolve().is_relative_to((folder/name).resolve()):
                    raise ValueError('Package manifest escapes root')
                if not target.is_file() or sha(target.read_bytes()) != digest:
                    changed.append(path)
            packages[f'{folder.name}/{name}'] = {'manifest_sha256':sha(manifest_path.read_bytes()), 'manifest_mismatches':changed,
                'archive_sha256':sha((folder/(name+'.zip')).read_bytes()) if (folder/(name+'.zip')).exists() else None}
    text = (root/'endpoint/agent.py').read_text(encoding='utf-8')
    version = re.search(r'"agent_ver":\s*"([^"]+)"', text)
    return {'schema_version':1, 'scope':'Local source and generated artifacts; not guest deployment evidence',
            'root_git_present':(root/'.git').exists(), 'agent_reported_version':version[1] if version else None,
            'server_semantic_version':None, 'deployed_guest_versions':'not verified',
            'python':sys.version, 'platform':platform.platform(), 'sources':sources,
            'source_manifest_sha256':sha(json.dumps(sources,sort_keys=True).encode()),
            'baselines':baselines, 'packages':packages}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    report = inventory()
    with args.output.open('x',encoding='utf-8') as f:
        json.dump(report,f,indent=2)
    print('Source files:',len(report['sources']))
    print('Baseline integrity:',all(r['archive_matches'] and r['members_match'] for r in report['baselines'].values()))
    print('Package manifest mismatches:',sum(len(r['manifest_mismatches']) for r in report['packages'].values()))
