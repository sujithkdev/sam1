import copy
import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('phase9', Path(__file__).resolve().parents[1]/'tools/phase9_dataset.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def sample(root):
    for name in ('protocol.md', 'truth.txt', 'collector.xml'):
        (root/name).write_text('Synthetic test artifact only')
    event = dict(event='process_spawn', event_id='test-event-1', system_id='test-host',
                 exe_path=r'C:\Windows\System32\vssadmin.exe', cmdline='vssadmin delete shadows /all')
    (root/'trace.jsonl').write_text(json.dumps(event)+'\n')
    return dict(schema_version=1, evidence_kind='synthetic_test', dataset_id='test-only',
                label_method='synthetic fixture', reviewer='test', matching_policy='test', protocol='protocol.md',
                scenarios=[dict(scenario_id='one', leakage_group='family1', host_id='test-host',
                                collector_version='fixture', ground_truth_method='test fixture',
                                split='held_out', label='malicious', execution_succeeded=True,
                                trace='trace.jsonl', ground_truth_artifact='truth.txt', collector_configuration='collector.xml')])


def test_freeze_verify_replay(tmp_path):
    manifest = module.freeze(tmp_path, sample(tmp_path))
    assert module.verify(tmp_path, manifest) == manifest
    result = module.replay(tmp_path, manifest)
    assert result['evidence_kind'] == 'synthetic_test'
    assert len(result['scenarios'][0]['findings']) == 1
    assert result['scenarios'][0]['supported_events'] == 1
    assert len(result['adapter_sha256']) == 64


@pytest.mark.parametrize('name', ['trace.jsonl', 'truth.txt', 'collector.xml', 'protocol.md'])
def test_modified_artifact_rejected(tmp_path, name):
    manifest = module.freeze(tmp_path, sample(tmp_path))
    with (tmp_path/name).open('a') as stream:
        stream.write(' ')
    with pytest.raises(ValueError, match='changed'):
        module.verify(tmp_path, manifest)


def test_path_traversal_rejected(tmp_path):
    document = sample(tmp_path)
    document['scenarios'][0]['trace'] = '../outside.jsonl'
    with pytest.raises(ValueError, match='escapes'):
        module.freeze(tmp_path, document)


def test_leakage_even_with_different_formatting(tmp_path):
    document = sample(tmp_path)
    event = json.loads((tmp_path/'trace.jsonl').read_text())
    (tmp_path/'second.jsonl').write_text(json.dumps(event, separators=(',', ':')))
    second = copy.deepcopy(document['scenarios'][0])
    second.update(scenario_id='two', leakage_group='different', split='tuning', trace='second.jsonl')
    document['scenarios'].append(second)
    with pytest.raises(ValueError, match='leakage'):
        module.freeze(tmp_path, document)


def test_failed_emulation_excluded(tmp_path):
    document = sample(tmp_path)
    document['scenarios'][0].update(execution_succeeded=False, invalidity_reason='fixture failure')
    result = module.replay(tmp_path, module.freeze(tmp_path, document))
    assert result['scenarios'][0]['state'] == 'excluded_failed_execution'


def test_wrong_host_and_duplicate_events_rejected(tmp_path):
    document = sample(tmp_path)
    document['scenarios'][0]['host_id'] = 'other'
    with pytest.raises(ValueError, match='different host'):
        module.freeze(tmp_path, document)
    document['scenarios'][0]['host_id'] = 'test-host'
    content = (tmp_path/'trace.jsonl').read_text()
    (tmp_path/'trace.jsonl').write_text(content+content)
    with pytest.raises(ValueError, match='Duplicate event'):
        module.freeze(tmp_path, document)


def test_unsupported_events_reported(tmp_path):
    document = sample(tmp_path)
    (tmp_path/'trace.jsonl').write_text(json.dumps(dict(event='network_connect',event_id='n',system_id='test-host')))
    result = module.replay(tmp_path, module.freeze(tmp_path, document))['scenarios'][0]
    assert result['unsupported_events'] == 1 and result['supported_events'] == 0
    assert not result['findings']
