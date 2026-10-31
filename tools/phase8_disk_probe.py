"""Real ENOSPC in a disposable 16 MiB Docker tmpfs, never on a host filesystem."""
import argparse
import json
from pathlib import Path
import subprocess

PROGRAM = r'''
import errno,json,os,sqlite3,sys,time
sys.path.insert(0,'/app/backend')
os.environ.update(EDR_ENV='test',EDR_JWT_SECRET='disk-probe-only-'+'z'*64,
    EDR_DATA_DIR='/fault',EDR_BACKGROUND='false',EDR_MIN_FREE_BYTES='0')
from server import create_app
from server.ingestion import accept,process_one
from server.database.storage import _conn
from server.operations import storage_status
app=create_app()
filler='/fault/filler'
enospc=False
try:
    with open(filler,'wb',buffering=0) as stream:
        while True:
            stream.write(b'x'*1048576)
except OSError as exc:
    assert exc.errno==errno.ENOSPC,exc
    enospc=True
event=dict(system_id='fault',event='file_event',event_id='disk-fault-00000000000000',
           time=time.time(),file_path='x'*60000)
try:
    accept([event])
except OverflowError:
    rejected='storage_admission'
except sqlite3.OperationalError as exc:
    assert exc.sqlite_errorcode==sqlite3.SQLITE_FULL,exc
    rejected='sqlite_full'
else:
    raise AssertionError('Full volume accepted input')
assert _conn().execute('SELECT COUNT(*) FROM telemetry').fetchone()[0]==0
os.unlink(filler)
accept([event])
assert process_one()
assert _conn().execute('PRAGMA integrity_check').fetchone()[0]=='ok'
assert app.test_client().get('/ready').status_code==200
print('FAULT_RESULT='+json.dumps(dict(real_enospc=enospc,rejection=rejected,
    no_partial_batch=True,recovered_after_space_released=True,integrity='ok')))
'''


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    with args.output.open('x', encoding='utf-8') as stream:
        stream.write('{"status":"running"}')
    result = subprocess.run(['docker','run','--rm','-i','--network','none','--read-only',
                             '--cap-drop','ALL','--security-opt','no-new-privileges',
                             '--tmpfs','/fault:rw,size=16m,mode=1777',
                             'behedr-phase2-server','python','-'], input=PROGRAM,
                            text=True,capture_output=True,timeout=90)
    lines = [line for line in result.stdout.splitlines() if line.startswith('FAULT_RESULT=')]
    if result.returncode or not lines:
        args.output.write_text(json.dumps({'status':'failed','error':result.stderr[-2000:]}))
        raise SystemExit('Fault probe failed; see output artifact')
    report = {'status':'completed','scope':'16 MiB disposable tmpfs, synthetic event',
              'checks':json.loads(lines[-1].split('=',1)[1])}
    args.output.write_text(json.dumps(report,indent=2))
    print('Real ENOSPC, rejection, recovery and integrity: passed')
