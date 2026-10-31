import copy
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('phase7', Path(__file__).resolve().parents[1] / 'tools/phase7_evaluate.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def data():
    variant = {'description': 'Test fixture only', 'code_sha256': 'a'*64, 'rules_sha256': 'b'*64,
               'configuration_sha256': 'c'*64, 'feature_switches': {}}
    row = dict(run_id='r1', variant='full', split='held_out', leakage_group='group1', trace_sha256='d'*64,
               host_id='test', scenario_id='scenario1', ground_truth_method='independent fixture',
               reviewer='test', collector_version='test', collector_configuration_sha256='e'*64,
               label='malicious', execution_succeeded=True, detected=True, alert_count=2,
               true_alerts=1, false_alerts=1, unadjudicated_alerts=0, expected_events=10,
               observed_events=8, attributed_events=6, benign_endpoint_hours=0, latency_seconds=3)
    return dict(schema_version=1, evidence_kind='synthetic_test', protocol_id='test',
                protocol_sha256='f'*64, matching_policy='fixture', variants={'full': variant}, runs=[row])


def test_metrics_denominators():
    report = module.evaluate(data())
    assert not report['comparisons']['held_out']['paired_inputs_complete']
    result = report['metrics']['full/held_out']
    assert result['scenario_recall'] == 1
    assert result['adjudicated_alert_precision'] == .5
    assert result['collection_recall'] == .8
    assert result['attribution_completeness'] == .75
    assert result['alerts_per_benign_endpoint_day'] is None
    assert result['latency_detected_only_p95_seconds'] == 3


def test_empty_is_not_run():
    document = data()
    document['runs'] = []
    result = module.evaluate(document)
    assert result['status'] == 'not_run'
    assert result['metrics'] == {}


def test_failed_emulation_excluded():
    document = data()
    document['runs'][0].update(execution_succeeded=False, invalidity_reason='operation failed')
    metrics = module.evaluate(document)['metrics']['full/held_out']
    assert metrics['valid_runs'] == 0 and metrics['excluded_failed_runs'] == 1
    assert metrics['scenario_recall'] is None


@pytest.mark.parametrize('field,value', [('latency_seconds', float('nan')), ('expected_events', True),
    ('true_alerts', 3), ('observed_events', 11), ('detected', False), ('trace_sha256', 'bad')])
def test_invalid_measurements_rejected(field, value):
    document = data()
    document['runs'][0][field] = value
    with pytest.raises(ValueError):
        module.evaluate(document)


@pytest.mark.parametrize('same_group', [True, False])
def test_split_leakage_rejected(same_group):
    document = data()
    second = copy.deepcopy(document['runs'][0])
    second.update(run_id='r2', split='tuning')
    if same_group:
        second['trace_sha256'] = '1'*64
    else:
        second['leakage_group'] = 'different'
    document['runs'].append(second)
    with pytest.raises(ValueError, match='leakage'):
        module.evaluate(document)


def test_comparisons_require_equal_inputs():
    document = data()
    document['variants']['baseline'] = copy.deepcopy(document['variants']['full'])
    assert not module.evaluate(document)['comparisons']['held_out']['paired_inputs_complete']
    row = copy.deepcopy(document['runs'][0])
    row['variant'] = 'baseline'
    document['runs'].append(row)
    assert module.evaluate(document)['comparisons']['held_out']['paired_inputs_complete']
    row['trace_sha256'] = '2'*64
    with pytest.raises(ValueError, match='different input'):
        module.evaluate(document)


def test_benign_exposure_and_unadjudicated_alerts():
    document = data()
    document['runs'][0].update(label='benign', detected=False, true_alerts=0, false_alerts=1,
                               unadjudicated_alerts=1, latency_seconds=None, benign_endpoint_hours=12)
    metrics = module.evaluate(document)['metrics']['full/held_out']
    assert metrics['alerts_per_benign_endpoint_day'] == 4
    assert metrics['unadjudicated_alerts'] == 1
    assert metrics['scenario_recall'] is None


def test_duplicate_run_rejected():
    document = data()
    document['runs'].append(copy.deepcopy(document['runs'][0]))
    with pytest.raises(ValueError, match='duplicate'):
        module.evaluate(document)
