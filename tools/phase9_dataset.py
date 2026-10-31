"""Freeze and verify labeled telemetry manifests; replay only the strict Sigma baseline."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from server.core import sigma_subset

MAX_TRACE_BYTES = 64 * 1024 * 1024


def contained(root, name):
    if not isinstance(name, str) or not name or Path(name).is_absolute():
        raise ValueError('Artifact paths must be relative to the dataset directory')
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError('Artifact escapes dataset root or is missing')
    return path


def read_trace(path):
    if path.stat().st_size > MAX_TRACE_BYTES:
        raise ValueError('Trace exceeds 64 MiB limit')
    raw = path.read_bytes()
    events = []
    identities = set()
    for line in raw.decode('utf-8-sig').splitlines():
        if not line.strip():
            continue
        if len(line.encode()) > 65536:
            raise ValueError('Event exceeds 64 KiB')
        event = json.loads(line)
        if not isinstance(event, dict):
            raise ValueError('Each event must be an object')
        for key in ('event', 'system_id', 'event_id'):
            if not isinstance(event.get(key), str) or not event[key]:
                raise ValueError('Missing event identity/type')
        identity = (event['system_id'], event['event_id'])
        if identity in identities:
            raise ValueError('Duplicate event identity within trace')
        identities.add(identity)
        for key in ('exe_path', 'cmdline', 'parent_exe_path'):
            if key in event and not isinstance(event[key], str):
                raise ValueError('Mapped Sigma fields must be strings')
        events.append(event)
    if not events:
        raise ValueError('Empty trace')
    # Formatting-independent hash catches reserialized duplicates across splits.
    canonical = json.dumps(sorted(events, key=lambda e: (e['system_id'], e['event_id'])),
                           sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return raw, events, hashlib.sha256(canonical).hexdigest()


def freeze(root, specification):
    if specification.get('schema_version') != 1 or specification.get('evidence_kind') not in {'live_lab', 'synthetic_test'}:
        raise ValueError('Explicit supported schema/evidence kind required')
    for key in ('dataset_id', 'label_method', 'reviewer', 'matching_policy'):
        if not isinstance(specification.get(key), str) or not specification[key].strip():
            raise ValueError('Missing dataset metadata: ' + key)
    protocol = contained(root, specification.get('protocol'))
    scenarios = specification.get('scenarios')
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError('Nonempty scenario registry required')
    groups, hashes, identities, seen, output = {}, {}, {}, set(), []
    for scenario in scenarios:
        for key in ('scenario_id', 'leakage_group', 'host_id', 'collector_version', 'ground_truth_method'):
            if not isinstance(scenario.get(key), str) or not scenario[key].strip():
                raise ValueError('Missing scenario metadata: ' + key)
        sid = scenario['scenario_id']
        if sid in seen:
            raise ValueError('Duplicate scenario ID')
        seen.add(sid)
        split = scenario.get('split')
        if split not in {'tuning', 'held_out'} or scenario.get('label') not in {'benign', 'malicious'}:
            raise ValueError('Invalid split or independent label')
        if type(scenario.get('execution_succeeded')) is not bool:
            raise ValueError('Explicit execution outcome required')
        if not scenario['execution_succeeded'] and not scenario.get('invalidity_reason'):
            raise ValueError('Failed execution needs an invalidity reason')
        trace = contained(root, scenario.get('trace'))
        raw, events, canonical = read_trace(trace)
        if any(e['system_id'] != scenario['host_id'] for e in events):
            raise ValueError('Trace contains a different host')
        for mapping, key in ((groups, scenario['leakage_group']), (hashes, canonical)):
            if key in mapping and mapping[key] != split:
                raise ValueError('Tuning/held-out leakage')
            mapping[key] = split
        for event in events:
            key = (event['system_id'], event['event_id'])
            if key in identities and identities[key] != split:
                raise ValueError('Event identity overlaps tuning and held-out splits')
            identities[key] = split
        artifacts = {}
        for key in ('ground_truth_artifact', 'collector_configuration'):
            artifact = contained(root, scenario.get(key))
            artifacts[key] = hashlib.sha256(artifact.read_bytes()).hexdigest()
        output.append({**scenario, 'trace_sha256': hashlib.sha256(raw).hexdigest(),
                       'canonical_trace_sha256': canonical, 'event_count': len(events),
                       'artifact_sha256': artifacts})
    return {**specification, 'protocol_sha256': hashlib.sha256(protocol.read_bytes()).hexdigest(),
            'scenarios': output, 'status': 'integrity_frozen_not_independently_audited'}


def verify(root, manifest):
    rebuilt = freeze(root, manifest)
    if rebuilt != manifest:
        raise ValueError('Dataset changed since freeze')
    return rebuilt


def replay(root, manifest):
    verify(root, manifest)
    sigma_subset.load_catalog()
    outcomes = []
    for scenario in manifest['scenarios']:
        raw, events, _ = read_trace(contained(root, scenario['trace']))
        if hashlib.sha256(raw).hexdigest() != scenario['trace_sha256']:
            raise ValueError('Trace changed during replay')
        if not scenario['execution_succeeded']:
            outcomes.append({'scenario_id': scenario['scenario_id'], 'state': 'excluded_failed_execution'})
            continue
        matches, supported = [], 0
        for event in events:
            # Consume normalized process telemetry only. Do not guess other-source mappings.
            if event['event'] != 'process_spawn':
                continue
            supported += 1
            assessment = sigma_subset.evaluate(event)
            if assessment['matches']:
                matches.append({'event_id': event['event_id'], 'system_id': event['system_id'],
                                'matches': assessment['matches']})
        outcomes.append({'scenario_id': scenario['scenario_id'], 'state': 'replayed',
                         'split': scenario['split'], 'trace_sha256': scenario['trace_sha256'],
                         'supported_events': supported, 'unsupported_events': len(events)-supported,
                         'findings': matches})
    return {'schema_version': 1, 'dataset_id': manifest['dataset_id'],
            'evidence_kind': manifest['evidence_kind'], 'adapter': 'behedr-sigma-subset-v1',
            'manifest_sha256': hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest(),
            'adapter_sha256': hashlib.sha256(Path(sigma_subset.__file__).read_bytes()).hexdigest(),
            'catalog': {r['id']: r['sha256'] for r in sigma_subset.RULES},
            'scenarios': outcomes,
            'limitations': ['Rule-only replay, not full BehEDR or an external Sigma engine.',
                            'Findings require independent adjudication before Phase 7 metrics.',
                            'No command execution, online latency measurement or malware-accuracy claim.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['freeze', 'verify', 'replay-sigma'])
    parser.add_argument('input', type=Path)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    document = json.loads(args.input.read_text(encoding='utf-8-sig'))
    if args.action == 'verify':
        verify(args.root, document)
        print('Integrity verified; label quality still requires independent audit.')
    else:
        if args.output is None:
            parser.error('--output is required for freeze and replay-sigma')
        result = freeze(args.root, document) if args.action == 'freeze' else replay(args.root, document)
        with args.output.open('x', encoding='utf-8') as stream:
            json.dump(result, stream, indent=2, allow_nan=False)
        print('Artifact saved; evidence kind and scope are explicit in the result.')
