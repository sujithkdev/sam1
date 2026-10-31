"""Create isolated lab configuration without replacing existing credentials."""
from pathlib import Path
import secrets

root = Path(__file__).resolve().parents[1]
directory = root / 'var/phase2'
directory.mkdir(parents=True, exist_ok=True)
environment = directory / 'lab.env'
if not environment.exists():
    with environment.open('x', encoding='utf-8') as stream:
        stream.write('EDR_JWT_SECRET=' + secrets.token_urlsafe(64) + '\n')
        stream.write('BEHEDR_CADDY_IMAGE=caddy:2@sha256:3095ad245c353e3bdb27a38f22a095c1cfa9e295ab21c0214c3e72b0e2960525\n')
print('Lab configuration ready; credentials preserved and not printed.')
