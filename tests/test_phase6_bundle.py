import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('phase6_review', Path(__file__).resolve().parents[1] / 'tools/phase6_review_bundle.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def bundle(tmp_path, exit_code=0):
    # Synthetic fixtures exercise the reviewer only; never counted as lab evidence.
    xml = '''<Events><Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
    <System><EventID>1</EventID><EventRecordID>2</EventRecordID>
    <TimeCreated SystemTime="2026-01-01T12:00:01Z"/></System><EventData>
    <Data Name="ProcessId">12</Data><Data Name="Image">C:\\Windows\\System32\\vssadmin.exe</Data>
    <Data Name="CommandLine">vssadmin list shadows</Data></EventData></Event></Events>'''
    (tmp_path / 'sysmon.xml').write_text(xml)
    scenarios = [{'name': 'shadow-list', 'label': 'benign', 'pid': 12,
                  'image': r'C:\Windows\System32\vssadmin.exe', 'exit_code': exit_code,
                  'started': '2026-01-01T12:00:00Z', 'ended': '2026-01-01T12:00:02Z'}]
    (tmp_path / 'scenarios.json').write_text(json.dumps(scenarios))
    manifest = {'format': 'behedr-phase6-guest-v1', 'run_id': 'test-only', 'host': 'test-host',
                'event_count': 1, 'sha256': {name: hashlib.sha256((tmp_path / name).read_bytes()).hexdigest()
                                          for name in ('sysmon.xml', 'scenarios.json')}}
    (tmp_path / 'manifest.json').write_text(json.dumps(manifest))


def test_bundle_review_preserves_scope(tmp_path):
    bundle(tmp_path)
    result = module.review(tmp_path)
    assert result['malware_accuracy'] is None
    assert result['scenarios'][0]['state'] == 'observed'
    assert not result['scenarios'][0]['events'][0]['assessment']['matches']


def test_failed_command_is_inconclusive(tmp_path):
    bundle(tmp_path, exit_code=1)
    assert module.review(tmp_path)['scenarios'][0]['state'] == 'inconclusive'


def test_changed_evidence_rejected(tmp_path):
    bundle(tmp_path)
    (tmp_path / 'sysmon.xml').write_text('<Events/>')
    with pytest.raises(ValueError, match='checksum'):
        module.review(tmp_path)
