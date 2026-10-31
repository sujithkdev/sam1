import importlib.util
from pathlib import Path
import sqlite3

from spool import Spool

spec = importlib.util.spec_from_file_location('lab_status', Path(__file__).resolve().parents[1]/'tools/lab_status.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_missing_database_is_not_created(tmp_path):
    path = tmp_path/'missing.db'
    try:
        module.inspect_database(path, 'agent')
    except sqlite3.OperationalError:
        pass
    else:
        raise AssertionError('Missing database should fail')
    assert not path.exists()


def test_private_payload_is_not_exported(tmp_path):
    path = tmp_path/'agent.db'
    spool = Spool(path)
    spool.put('/events', {'event_id':'test', 'cmdline':'private command'})
    spool.commit_source('transport', {'state':'acknowledged','last_ack_at':123,'secret':'private token'})
    result = module.inspect_database(path, 'agent')
    assert result['queued'] == 1
    assert result['transport'] == {'state':'acknowledged','last_ack_at':123}
    assert 'private' not in str(result)
    assert spool.stats()['queued'] == 1
    spool.conn.close()
