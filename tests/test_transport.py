import sqlite3
import time
from unittest.mock import Mock

import pytest
import requests
from spool import Spool
from transport import Sender


def reply(code, data=None):
    return Mock(status_code=code, json=Mock(return_value=data))


def test_failed_route_does_not_stop_other_telemetry(tmp_path):
    spool = Spool(tmp_path/'fair.db')
    spool.put('/file_events', {'event_id':'file-pending'})
    spool.put('/events', {'event_id':'process-pending'})
    calls = []
    def post(url, **kwargs):
        calls.append(url)
        if url.endswith('/file_events'):
            return reply(503)
        return reply(200, {'accepted':[e['event_id'] for e in kwargs['json']['events']]})
    sender = Sender(spool, 'https://lab', {}, post=post)
    assert sender.cycle() == 'server_backpressure'
    assert sender.cycle() == 'acknowledged'
    assert spool.stats()['queued'] == 1
    assert sender.cycle() == 'server_backpressure'
    assert calls == ['https://lab/file_events','https://lab/events','https://lab/file_events']
    sender.post = lambda url, **kw: reply(200, {'accepted':['file-pending']})
    assert sender.cycle() == 'acknowledged'
    assert spool.stats()['queued'] == 0
    spool.conn.close()


def test_busy_route_does_not_starve_other_routes(tmp_path):
    spool = Spool(tmp_path/'busy.db')
    for i in range(205):
        spool.put('/file_events', {'event_id':f'file-{i}'})
    spool.put('/events', {'event_id':'process'})
    sender = Sender(spool, 'https://lab', {}, post=lambda url, **kw: reply(
        200, {'accepted':[e['event_id'] for e in kw['json']['events']]}))
    assert sender.cycle() == 'acknowledged'
    assert spool.stats()['queued'] == 106
    assert sender.cycle() == 'acknowledged'
    assert spool.source_state('transport')['route'] == '/events'
    assert spool.stats()['queued'] == 105
    spool.conn.close()


def test_lost_ack_reopen_reconnect_and_dedup(tmp_path, client, agent_headers, event):
    from server.database.storage import _conn
    from server.ingestion import process_one
    path = tmp_path/'outbox.db'
    spool = Spool(path)
    spool.put('/events', event)
    def lost_ack(url, **kw):
        response = client.post('/events', json=kw['json'], headers=agent_headers)
        assert response.status_code == 200
        raise requests.ReadTimeout('simulated lost acknowledgment after commit')
    sender = Sender(spool, 'http://localhost', agent_headers, post=lost_ack)
    assert sender.cycle() == 'response_timeout'
    assert spool.stats()['queued'] == 1
    assert _conn().execute('SELECT COUNT(*) FROM telemetry').fetchone()[0] == 1
    spool.conn.close()
    spool = Spool(path)
    assert spool.source_state('transport')['state'] == 'response_timeout'
    def deliver(url, **kw):
        response = client.post('/events', json=kw['json'], headers=agent_headers)
        return reply(response.status_code,response.json)
    sender = Sender(spool,'http://localhost',agent_headers,post=Mock(side_effect=requests.ConnectionError()))
    assert sender.cycle() == 'connection_error'
    assert spool.stats()['queued'] == 1
    sender.post = deliver
    assert sender.cycle() == 'acknowledged'
    assert spool.stats()['queued'] == 0
    assert spool.source_state('transport')['last_ack_at'] > 0
    assert _conn().execute('SELECT COUNT(*) FROM telemetry').fetchone()[0] == 1
    # Receipt acknowledgment precedes analysis.
    assert _conn().execute('SELECT COUNT(*) FROM events').fetchone()[0] == 0
    assert process_one()
    assert _conn().execute('SELECT COUNT(*) FROM events').fetchone()[0] == 1
    assert not process_one()
    spool.conn.close()


@pytest.mark.parametrize('code,state',[(401,'authentication_rejected'),(403,'authentication_rejected'),(429,'server_backpressure'),(503,'server_backpressure'),(500,'http_error'),(302,'http_error')])
def test_transient_and_auth_failures_retain(tmp_path,code,state):
    spool=Spool(tmp_path/'outbox.db')
    spool.put('/events',{'event_id':'a'*32})
    sender=Sender(spool,'http://localhost',{},post=Mock(return_value=reply(code)))
    assert sender.cycle()==state
    assert spool.stats()['queued']==1
    assert sender.post.call_args.kwargs['allow_redirects'] is False
    spool.conn.close()


@pytest.mark.parametrize('accepted',[None,{},['foreign-id'],'a'*32,[{}]])
def test_bad_ack_never_deletes(tmp_path,accepted):
    spool=Spool(tmp_path/'outbox.db')
    spool.put('/events',{'event_id':'a'*32})
    sender=Sender(spool,'http://localhost',{},post=Mock(return_value=reply(200,{'accepted':accepted})))
    assert sender.cycle()=='invalid_acknowledgment'
    assert spool.stats()['queued']==1
    spool.conn.close()


def test_partial_ack_and_rejected_batch(tmp_path):
    spool=Spool(tmp_path/'outbox.db')
    for identity in ('a'*32,'b'*32):spool.put('/events',{'event_id':identity})
    sender=Sender(spool,'http://localhost',{},post=Mock(return_value=reply(200,{'accepted':['a'*32]})))
    assert sender.cycle()=='partial_acknowledgment'
    assert spool.peek()[1][0]['event_id']=='b'*32
    spool.put('/events',{'event_id':'c'*32})
    sender.post=Mock(side_effect=[reply(400),reply(400),reply(200,{'accepted':['c'*32]})])
    assert sender.cycle()=='batch_isolated'
    assert spool.stats()=={'queued':0,'rejected':1}
    spool.conn.close()


def test_queue_migration_unknown_age_and_bookmark(tmp_path):
    path=tmp_path/'old.db'
    conn=sqlite3.connect(path)
    conn.execute("CREATE TABLE outbox(id INTEGER PRIMARY KEY,path TEXT,event_id TEXT UNIQUE,payload TEXT,error TEXT DEFAULT '')")
    conn.execute("INSERT INTO outbox(path,event_id,payload) VALUES('/events','old','{}')")
    conn.commit();conn.close()
    spool=Spool(path)
    assert spool.diagnostics()['unknown_enqueue_count']==1
    assert spool.diagnostics()['oldest_known_age_seconds'] is None
    spool.commit_source('sysmon',{'record_id':1},[('/events',{'event_id':'new'})])
    diagnostics=spool.diagnostics()
    assert diagnostics['queued']==2 and diagnostics['oldest_known_age_seconds']>=0
    timestamp=diagnostics['oldest_known_enqueue_at']
    spool.conn.close();spool=Spool(path)
    assert spool.diagnostics()['oldest_known_enqueue_at']==timestamp
    spool.conn.close()

def test_http_delivery_across_server_and_agent_restart(tmp_path, event):
    """Real loopback HTTP + fresh server processes, synthetic events, no collectors."""
    import os
    from pathlib import Path
    import socket
    import subprocess
    import sys
    from server.config import BASE_DIR
    sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1];sock.close()
    state=tmp_path/'server'
    code='''
import os,sys
sys.path.insert(0,os.environ['R1_BACKEND'])
from server import create_app
from server.auth import enroll_agent
from pathlib import Path
from waitress import serve
app=create_app()
token_file = Path(os.environ['R1_TOKEN_FILE'])
if not token_file.exists():
    token_file.write_text(enroll_agent('test-host'))
serve(app,host='127.0.0.1',port=int(os.environ['R1_PORT']),threads=4)
'''
    root=Path(__file__).resolve().parents[1]
    token_path=tmp_path/'token'
    env={**os.environ,'EDR_DATA_DIR':str(state),'EDR_BACKGROUND':'true',
         'R1_BACKEND':str(root/'backend'),'R1_TOKEN_FILE':str(token_path),'R1_PORT':str(port)}
    base=f'http://127.0.0.1:{port}'
    processes=[]
    log=open(tmp_path/'server.log','w')
    spool=Spool(tmp_path/'agent.db')
    session=requests.Session();session.trust_env=False
    def start():
        process=subprocess.Popen([sys.executable,'-c',code],env=env,stdout=log,stderr=log)
        processes.append(process)
        end=time.monotonic()+40
        while time.monotonic()<end:
            assert process.poll() is None, (tmp_path/'server.log').read_text()
            try:
                if token_path.exists() and session.get(base+'/ready',timeout=1).status_code==200:
                    return {'API-Key':token_path.read_text()}
            except requests.RequestException:pass
            time.sleep(.1)
        raise AssertionError('Server did not become ready')
    try:
        headers=start()
        spool.put('/events',event)
        def drop_response(url,**kw):
            response=session.post(url,**kw)
            assert response.status_code==200
            raise requests.ReadTimeout('test deliberately discards committed response')
        sender=Sender(spool,base,headers,post=drop_response)
        assert sender.cycle()=='response_timeout'
        processes[-1].terminate();processes[-1].wait(timeout=10)
        spool.conn.close();spool=Spool(tmp_path/'agent.db')
        sender=Sender(spool,base,headers,timeout=1,post=session.post)
        assert sender.cycle() in {'connection_error', 'connect_timeout'}
        assert spool.stats()['queued'] == 1
        headers=start()  # Restart preserves the same endpoint credential.
        sender.headers=headers
        assert sender.cycle()=='acknowledged'
        end=time.monotonic()+15
        while time.monotonic()<end:
            with sqlite3.connect(state/'edr.db') as c:
                rows=c.execute('SELECT COUNT(*),SUM(status=\'done\') FROM telemetry WHERE event_id=?',(event['event_id'],)).fetchone()
                count=c.execute('SELECT COUNT(*) FROM events WHERE event_id=?',(event['event_id'],)).fetchone()[0]
            if rows==(1,1) and count==1:break
            time.sleep(.1)
        assert rows==(1,1) and count==1
        assert spool.stats()=={'queued':0,'rejected':0}
    finally:
        for process in processes:
            if process.poll() is None:process.terminate();process.wait(timeout=10)
        spool.conn.close();session.close();log.close()
