"""Inert scoring regressions; no file watcher, malware or response execution."""
import json
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

import pytest

from server.core.file_behavior import load_rules, score_events


RULE_PATH = Path(__file__).resolve().parents[1] / "rules" / "file_behavior.json"


def observations(paths):
    return [{"path": path, "action": "modify"} for path in paths]


def test_readme_alone_does_not_classify_as_ransomware():
    events = observations(["C:/Docs/README.txt"] + [f"C:/Docs/notes{i}.txt" for i in range(4)])
    assert score_events(events, load_rules(RULE_PATH)) == (0, [])


def test_repeated_same_file_does_not_become_mass_modification():
    assert score_events(observations(["C:/Docs/README.txt"] * 60), load_rules(RULE_PATH)) == (0, [])


def test_bulk_activity_is_retained_and_score_is_bounded():
    rules = load_rules(RULE_PATH)
    score, reasons = score_events(observations([f"C:/Docs/{i}.txt" for i in range(21)]), rules)
    assert score == 60 and len(reasons) == 1
    score, reasons = score_events(
        observations([f"C:/Docs/{i}.locked" for i in range(51)] + ["C:/Docs/README.txt"]), rules)
    assert score == 100
    assert len(reasons) == 3
    assert not any("Ransom note:" in reason for reason in reasons)


def test_directory_name_is_not_note_evidence():
    score, reasons = score_events(
        observations([f"C:/Recovery/{i}.txt" for i in range(21)]), load_rules(RULE_PATH))
    assert score == 60 and len(reasons) == 1


def test_extension_evidence_requires_distinct_files():
    rules = load_rules(RULE_PATH)
    assert score_events(observations(["C:/Docs/a.enc"] * 5), rules) == (0, [])
    assert score_events(observations([f"C:/Docs/{i}.enc" for i in range(5)]), rules)[0] == 85


@pytest.mark.parametrize("key,value", [
    ("note_bonus", 101), ("minimum_events", True), ("window_seconds", 0),
    ("mass_modifications", 10), ("minimum_extension_files", 1),
    ("note_keywords", "readme"), ("note_extensions", ["txt"]), ("unknown", 1),
])
def test_invalid_rules_are_rejected(tmp_path, key, value):
    rules = json.loads(RULE_PATH.read_text())
    rules[key] = value
    path = tmp_path / "rules.json"
    path.write_text(json.dumps(rules))
    with pytest.raises(ValueError):
        load_rules(path)


def test_detector_window_and_process_filter(monkeypatch):
    from server.core import detector
    rules = load_rules(RULE_PATH)
    monkeypatch.setattr(detector, "_file_rules", rules)
    monkeypatch.setattr(detector, "time", SimpleNamespace(time=lambda: 1000))
    monkeypatch.setattr(detector, "_file_events", defaultdict(list))
    events = detector._file_events["file-test-host"]
    events.extend({**event, "process": "writer", "ts": 900}
                  for event in observations([f"C:/Docs/{i}.locked" for i in range(5)]))
    assert detector._l7_file("file-test-host", "writer")[0] == 85
    assert detector._l7_file("file-test-host", "another-writer") == (0, [])
    monkeypatch.setattr(detector, "time", SimpleNamespace(time=lambda: 1020))
    assert detector._l7_file("file-test-host", "writer") == (0, [])


def test_file_ingestion_uses_scorer(client, agent_headers, monkeypatch):
    from server.core import detector
    from server.ingestion import process_one
    from server.database.storage import get_alerts
    monkeypatch.setattr(detector, "_file_events", defaultdict(list))
    events = [{"system_id": "test-host", "event": "file_event", "process": "unknown",
               "file_path": path, "action": "modify", "event_id": f"fileintegration{i:016d}"}
              for i, path in enumerate(["C:/Docs/README.txt"] + [f"C:/Docs/{j}.txt" for j in range(4)])]
    response = client.post("/file_events", headers=agent_headers, json={"events": events})
    assert response.status_code == 200
    for _ in events:
        assert process_one()
    assert not get_alerts()
