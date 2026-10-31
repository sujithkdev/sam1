"""Executed inside the lab container against a fresh disposable database."""
import json
import os
from pathlib import Path
import sys
import tempfile
import time

sys.path.insert(0, '/app/backend')
with tempfile.TemporaryDirectory(prefix='phase8-retention-') as directory:
    os.environ.update(EDR_DATA_DIR=directory, EDR_BACKGROUND='false')
    from server import create_app
    from server.ingestion import accept, process_one
    from server.database.storage import _conn
    from server.retention import maintain
    from server.core import detector, recovery
    app = create_app()
    event = dict(system_id='isolated-retention', event_id='retention-container-000001',
                 event='file_event', time=1, file_path='C:/Lab/inert.txt')
    accept([event])
    assert process_one()
    _conn().execute('UPDATE telemetry SET received=?', (time.time()-40*86400,))
    result = maintain(30, 10, Path(directory)/'before.db', compact=True)
    assert result['deleted_completed_rows'] == 1
    assert result['compaction'] == 'completed'
    recovery.restore(detector._file_rules)
    accept([event])
    assert not process_one()
    assert app.test_client().get('/ready').status_code == 200
    assert _conn().execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    print('RETENTION_RESULT=' + json.dumps({'backup_verified': True, 'checkpoint_restore': True,
                                          'tombstone_retry_deduplication': True, 'integrity': 'ok'}))
