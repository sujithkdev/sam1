"""Review live guest smoke evidence offline. Never execute captured command lines."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'endpoint')]
from eventlog import parse_xml
from sysmon_collector import normalize
from server.core import sigma_subset


def review(folder):
    folder = Path(folder)
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8-sig'))
    if manifest.get('format') != 'behedr-phase6-guest-v1':
        raise ValueError('Unsupported bundle format')
    for name in ('sysmon.xml', 'scenarios.json'):
        if hashlib.sha256((folder / name).read_bytes()).hexdigest() != manifest['sha256'][name]:
            raise ValueError('Evidence checksum mismatch: ' + name)
    sigma_subset.load_catalog()
    records = parse_xml((folder / 'sysmon.xml').read_text(encoding='utf-8-sig'))
    if len(records) != manifest['event_count']:
        raise ValueError('Event count does not match manifest')
    events = []
    for record in records:
        if record['Event']['System']['EventID'] == 1:
            events.append(normalize(record, manifest['host'])[1])
    outcomes = []
    for scenario in json.loads((folder / 'scenarios.json').read_text(encoding='utf-8-sig')):
        start = datetime.fromisoformat(scenario['started']).timestamp()
        end = datetime.fromisoformat(scenario['ended']).timestamp()
        observed = [e for e in events if e['pid'] == scenario['pid']
                    and start <= e['time'] <= end
                    and e['exe_path'].casefold() == scenario['image'].casefold()]
        outcomes.append({'scenario': scenario['name'], 'label': scenario['label'],
                         'state': 'observed' if scenario['exit_code'] == 0 and observed else 'inconclusive',
                         'events': [{'event_id': e['event_id'], 'assessment': sigma_subset.evaluate(e)} for e in observed]})
    return {'scope': 'live-benign-smoke, Sigma subset only', 'run_id': manifest['run_id'],
            'scenarios': outcomes, 'malware_accuracy': None,
            'limitation': 'Not a full detector baseline comparison or calibration experiment'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('bundle', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = review(args.bundle)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
    print('Review saved; inconclusive scenarios require investigation.')
