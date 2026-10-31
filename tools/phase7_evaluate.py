"""Evaluate independently adjudicated scenario runs; never invent labels or execute traces."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics


def number(value, name, integer=False):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError('Invalid nonnegative number: ' + name)
    if integer and type(value) is not int:
        raise ValueError('Expected integer: ' + name)
    return value


def text(row, key):
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Missing text: ' + key)
    return value


def digest(value):
    if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
        raise ValueError('Expected lowercase SHA256')
    return value


def ratio(a, b):
    return a / b if b else None


def percentile(values, fraction):
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lo = math.floor(position)
    hi = math.ceil(position)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (position - lo)


def evaluate(document):
    if document.get('schema_version') != 1:
        raise ValueError('Unsupported schema_version')
    if document.get('evidence_kind') not in {'live_lab', 'synthetic_test'}:
        raise ValueError('Evidence kind must be explicit')
    text(document, 'protocol_id')
    text(document, 'matching_policy')
    digest(document.get('protocol_sha256'))
    variants = document.get('variants')
    if not isinstance(variants, dict) or not variants:
        raise ValueError('Named variants required')
    for name, variant in variants.items():
        if not isinstance(name, str) or not name:
            raise ValueError('Invalid variant name')
        for key in ('code_sha256', 'rules_sha256', 'configuration_sha256'):
            digest(variant.get(key))
        text(variant, 'description')
        if not isinstance(variant.get('feature_switches'), dict):
            raise ValueError('Explicit feature_switches required')
    rows = document.get('runs')
    if not isinstance(rows, list):
        raise ValueError('runs must be a list')
    seen = set()
    group_splits = {}
    trace_splits = {}
    inputs = {}
    grouped = {}
    for row in rows:
        run_id = text(row, 'run_id')
        variant = text(row, 'variant')
        if variant not in variants or (run_id, variant) in seen:
            raise ValueError('Unknown variant or duplicate run/variant')
        seen.add((run_id, variant))
        split = row.get('split')
        if split not in {'tuning', 'held_out'}:
            raise ValueError('Invalid split')
        group = text(row, 'leakage_group')
        trace = digest(row.get('trace_sha256'))
        for mapping, key in ((group_splits, group), (trace_splits, trace)):
            if key in mapping and mapping[key] != split:
                raise ValueError('Tuning/held-out leakage detected')
            mapping[key] = split
        for key in ('host_id', 'scenario_id', 'ground_truth_method', 'reviewer', 'collector_version'):
            text(row, key)
        digest(row.get('collector_configuration_sha256'))
        if row.get('label') not in {'benign', 'malicious'}:
            raise ValueError('Independent benign/malicious label required')
        if type(row.get('execution_succeeded')) is not bool or type(row.get('detected')) is not bool:
            raise ValueError('execution_succeeded and detected must be booleans')
        for key in ('alert_count', 'true_alerts', 'false_alerts', 'unadjudicated_alerts',
                    'expected_events', 'observed_events', 'attributed_events'):
            number(row.get(key), key, integer=True)
        if row['alert_count'] != sum(row[k] for k in ('true_alerts', 'false_alerts', 'unadjudicated_alerts')):
            raise ValueError('Alert adjudication totals do not reconcile')
        if row['label'] == 'benign' and row['true_alerts']:
            raise ValueError('Benign scenarios cannot have true attack alerts')
        if row['detected'] != (row['true_alerts'] > 0):
            raise ValueError('Detection requires at least one adjudicated true alert')
        if row['observed_events'] > row['expected_events'] or row['attributed_events'] > row['observed_events']:
            raise ValueError('Coverage counts must be matched unique expected events')
        number(row.get('benign_endpoint_hours'), 'benign_endpoint_hours')
        if row['label'] == 'malicious' and row['benign_endpoint_hours']:
            raise ValueError('Attack runs cannot contribute benign exposure')
        if row['execution_succeeded'] and row['label'] == 'benign' and not row['benign_endpoint_hours']:
            raise ValueError('Successful benign runs require measured exposure')
        latency = row.get('latency_seconds')
        if latency is not None:
            number(latency, 'latency_seconds')
        if row['execution_succeeded'] and row['detected'] and latency is None:
            raise ValueError('Detected scenarios require measured latency')
        if not row['detected'] and latency is not None:
            raise ValueError('Undetected scenarios cannot have detection latency')
        if not row['execution_succeeded']:
            text(row, 'invalidity_reason')
        # All compared variants must share ground truth, collection and exposure.
        shared = {k: row[k] for k in ('split', 'leakage_group', 'trace_sha256', 'host_id',
                  'scenario_id', 'label', 'execution_succeeded', 'expected_events', 'observed_events',
                  'collector_version', 'collector_configuration_sha256', 'benign_endpoint_hours')}
        if run_id in inputs and inputs[run_id] != shared:
            raise ValueError('Compared variants have different input/ground truth')
        inputs[run_id] = shared
        grouped.setdefault((variant, split), []).append(row)
    reports = {}
    for (variant, split), batch in sorted(grouped.items()):
        valid = [r for r in batch if r['execution_succeeded']]
        attacks = [r for r in valid if r['label'] == 'malicious']
        benign = [r for r in valid if r['label'] == 'benign']
        total = lambda key: sum(r[key] for r in valid)
        latencies = [r['latency_seconds'] for r in attacks if r['detected']]
        reports[variant + '/' + split] = {
            'valid_runs': len(valid), 'excluded_failed_runs': len(batch) - len(valid),
            'attack_scenarios': len(attacks), 'detected_scenarios': sum(r['detected'] for r in attacks),
            'scenario_recall': ratio(sum(r['detected'] for r in attacks), len(attacks)),
            'adjudicated_alert_precision': ratio(total('true_alerts'), total('true_alerts') + total('false_alerts')),
            'unadjudicated_alerts': total('unadjudicated_alerts'),
            'benign_endpoint_hours': sum(r['benign_endpoint_hours'] for r in benign),
            'alerts_per_benign_endpoint_day': ratio(sum(r['alert_count'] for r in benign) * 24,
                                                    sum(r['benign_endpoint_hours'] for r in benign)),
            'collection_recall': ratio(total('observed_events'), total('expected_events')),
            'attribution_completeness': ratio(total('attributed_events'), total('observed_events')),
            'latency_detected_only_median_seconds': statistics.median(latencies) if latencies else None,
            'latency_detected_only_p95_seconds': percentile(latencies, .95),
        }
    comparisons = {}
    for split in ('tuning', 'held_out'):
        sets = {v: {r['run_id'] for r in grouped.get((v, split), []) if r['execution_succeeded']} for v in variants}
        comparisons[split] = {'paired_inputs_complete': len(variants) >= 2 and bool(rows) and bool(next(iter(sets.values())))
                             and all(s == next(iter(sets.values())) for s in sets.values()),
                             'valid_runs_by_variant': {v: sorted(s) for v, s in sets.items()}}
    return {'schema_version': 1, 'evidence_kind': document['evidence_kind'],
            'protocol_id': document['protocol_id'], 'protocol_sha256': document['protocol_sha256'],
            'status': 'not_run' if not rows else 'computed_from_supplied_records',
            'variants': variants, 'metrics': reports, 'comparisons': comparisons,
            'limitations': ['Labels and artifact provenance require independent audit; hashes alone do not prove authenticity.',
                            'No significance, novelty or production-readiness conclusion is computed.',
                            'Precision excludes unadjudicated alerts; latency excludes missed detections.',
                            'Leakage groups must encode scenario/host/time or family constraints before running.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raw = args.input.read_bytes()
    report = evaluate(json.loads(raw))
    report['input_sha256'] = hashlib.sha256(raw).hexdigest()
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
    print('Evaluation written. Inspect evidence_kind, exclusions and comparison completeness before interpreting metrics.')
