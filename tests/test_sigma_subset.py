import copy
import json

import pytest
import yaml

from server.core import sigma_subset as sigma


def sample():
    return yaml.safe_load((sigma.CATALOG / 'shadow_deletion.yml').read_text())


@pytest.mark.parametrize('image,command,count', [
    (r'C:\Windows\System32\VSSADMIN.EXE', 'vssadmin delete shadows /all', 1),
    (r'C:\Windows\System32\vssadmin.exe', 'vssadmin list shadows', 0),
    (r'C:\Windows\System32\notepad.exe', 'delete shadows', 0),
    ('', 'vssadmin delete shadows', 0),
    (r'C:\Windows\System32\bcdedit.exe', 'bcdedit /set {default} recoveryenabled no', 1),
    (r'C:\Windows\System32\bcdedit.exe', 'bcdedit /enum', 0),
])
def test_catalog_examples(image, command, count):
    result = sigma.evaluate({'exe_path': image, 'cmdline': command})
    assert len(result['matches']) == count
    assert len(result['catalog']) == 2


@pytest.mark.parametrize('key,value', [
    ('CommandLine|re', '.*'), ('Unknown', 'abc'), ('CommandLine', '*delete*'),
    ('CommandLine|contains', None), ('CommandLine|contains', []),
    ('CommandLine|base64', 'abc'),
])
def test_reject_unsupported_fields(key, value):
    rule = sample()
    rule['detection']['selection'] = {key: value}
    with pytest.raises(ValueError):
        sigma.compile_rule(rule, 'digest')


@pytest.mark.parametrize('condition', ['selection or other', '1 of selection*', '__import__("os")', ['selection']])
def test_no_expression_execution(condition):
    rule = sample()
    rule['detection']['condition'] = condition
    with pytest.raises(ValueError):
        sigma.compile_rule(rule, 'digest')


def test_catalog_failure_is_atomic(tmp_path):
    before = sigma.RULES
    (tmp_path / 'bad.yml').write_text('!!python/object:os.system {}')
    with pytest.raises(yaml.YAMLError):
        sigma.load_catalog(tmp_path)
    assert sigma.RULES is before


def test_duplicate_ids_rejected(tmp_path):
    for name in ('one', 'two'):
        (tmp_path / (name + '.yml')).write_text(yaml.safe_dump(sample()))
    with pytest.raises(ValueError):
        sigma.load_catalog(tmp_path)


def test_duplicate_yaml_keys_rejected(tmp_path):
    (tmp_path / 'duplicate.yml').write_text('title: one\ntitle: two\n')
    with pytest.raises(ValueError, match='unique'):
        sigma.load_catalog(tmp_path)


def test_missing_parent_cannot_match(event):
    from server.core.processor import normalize
    rule = sample()
    rule['detection']['selection'] = {'ParentImage|endswith': r'\parent.exe'}
    original = sigma.RULES
    try:
        sigma.RULES = (sigma.compile_rule(rule, 'test'),)
        assert not sigma.evaluate(normalize(event))['matches']
        event['parent_exe_path'] = r'C:\Windows\parent.exe'
        assert len(sigma.evaluate(normalize(event))['matches']) == 1
    finally:
        sigma.RULES = original


def test_ingestion_persists_provenance(event):
    from server.ingestion import accept, process_one
    from server.database.storage import _conn
    event.update(child='vssadmin.exe', exe_path=r'C:\Windows\System32\vssadmin.exe',
                 cmdline='vssadmin delete shadows /all')
    accept([event])
    assert process_one()
    row = _conn().execute('SELECT status,assessment FROM telemetry').fetchone()
    assert row['status'] == 'done'
    hit = json.loads(row['assessment'])['sigma']['matches'][0]
    assert hit['author'] == 'BehEDR project' and len(hit['sha256']) == 64
    assert _conn().execute("SELECT COUNT(*) FROM alerts WHERE reason LIKE 'SIGMA %'").fetchone()[0] == 1
    accept([copy.deepcopy(event)])
    assert not process_one()
