"""Record installed dependency closure after a deliberate upgrade and test run."""
from importlib.metadata import distribution
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

root = Path(__file__).resolve().parents[1]


def lock(seeds, filename):
    pending, selected = list(seeds), {}
    while pending:
        name = canonicalize_name(pending.pop())
        if name in selected:
            continue
        dist = distribution(name)
        selected[name] = dist.version
        for specification in dist.requires or []:
            requirement = Requirement(specification)
            if requirement.marker is None or requirement.marker.evaluate({'extra': ''}):
                pending.append(requirement.name)
    text = '# Resolved from the tested Python 3.12 environment. Upgrade deliberately, then re-run tests and audit.\n'
    text += '\n'.join(f'{name}=={version}' for name, version in sorted(selected.items())) + '\n'
    (root / 'requirements' / filename).write_text(text, encoding='utf-8')


if __name__ == '__main__':
    server = ['Flask', 'PyJWT', 'PyYAML', 'networkx', 'numpy', 'requests', 'waitress']
    lock(server, 'server.lock')
    lock(server + ['psutil', 'pytest', 'ruff', 'pip-audit'], 'dev.lock')
