"""Isolated synthetic admission/drain measurements; never access the configured live database."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]


def worker(count, hosts, batch, output):
    sys.path.insert(0, str(ROOT / 'backend'))
    from server import create_app
    from server.ingestion import accept, process_one, backlog
    from server.database.storage import _conn
    from server.core import recovery, detector
    create_app()
    try:
        import psutil
        process = psutil.Process()
        memory = lambda: process.memory_info().rss
    except ImportError:
        memory = lambda: None
    start = time.time()
    events = []
    for i in range(count):
        base = dict(system_id=f'load-host-{i % hosts}', event_id=f'load-probe-{i:024}',
                    time=start+i/10000, pid=i+10, process='benign-probe.exe', process_guid=f'probe-{i // 30}')
        if i % 3 == 0:
            base.update(event='process_spawn', parent='explorer.exe', child='benign-probe.exe',
                        ppid=1, create_time=start, exe_path=r'C:\Lab\benign-probe.exe', cmdline='benign-probe')
        elif i % 3 == 1:
            base.update(event='file_event', file_path=f'C:/Lab/{i}.txt', action='modify')
        else:
            base.update(event='network_connect', remote_ip='8.8.8.8', remote_port=443)
        events.append(base)
    batches = [events[i:i+batch] for i in range(0, count, batch)]
    cpu = time.process_time()
    tick = time.perf_counter()
    with ThreadPoolExecutor(max_workers=hosts) as pool:
        list(pool.map(accept, batches))
    admission = time.perf_counter()-tick
    # Lost-ack retry storm: all duplicates must leave the queue unchanged.
    with ThreadPoolExecutor(max_workers=hosts) as pool:
        list(pool.map(accept, batches))
    assert backlog() == {'pending': count}
    durations = []
    sampled_rss = memory()
    tick = time.perf_counter()
    for _ in range(count):
        one = time.perf_counter()
        assert process_one()
        durations.append(time.perf_counter()-one)
        current = memory()
        if current is not None:
            sampled_rss = max(sampled_rss or 0, current)
    drain = time.perf_counter()-tick
    assert backlog() == {'done': count}, backlog()
    cpu_seconds = time.process_time()-cpu
    tick = time.perf_counter()
    recovery.restore(detector._file_rules)
    replay = time.perf_counter()-tick
    assert recovery.STATE['replayed'] == count
    assert _conn().execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    sizes = {suffix or 'database': Path(os.environ['EDR_DATA_DIR'], 'edr.db'+suffix).stat().st_size
             for suffix in ('', '-wal', '-shm') if Path(os.environ['EDR_DATA_DIR'], 'edr.db'+suffix).exists()}
    result = dict(events=count, simulated_hosts=hosts, batch_size=batch, admission_seconds=admission,
                  admission_events_per_second=count/admission, drain_seconds=drain,
                  drain_events_per_second=count/drain, cpu_seconds=cpu_seconds,
                  sampled_peak_rss_bytes=sampled_rss, replay_seconds=replay,
                  processing_median_seconds=statistics.median(durations),
                  processing_p95_seconds=sorted(durations)[int((len(durations)-1)*.95)],
                  sqlite_file_bytes=sizes, serialized_input_bytes=sum(len(json.dumps(e).encode()) for e in events),
                  retry_deduplication=True, integrity='ok')
    output.write_text(json.dumps(result, indent=2), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--events', type=int, default=300)
    parser.add_argument('--hosts', type=int, default=1)
    parser.add_argument('--batch', type=int, default=25)
    args = parser.parse_args()
    if args.worker:
        worker(args.events, args.hosts, args.batch, args.output)
        return
    # Reserve result path before doing work; never replace previous evidence.
    with args.output.open('x', encoding='utf-8') as stream:
        stream.write('{"status":"running"}')
    paths = sorted(p for directory in ('backend', 'rules') for p in (ROOT/directory).rglob('*')
                   if p.is_file() and p.suffix in {'.py', '.json', '.yaml', '.yml'})
    source = hashlib.sha256()
    for path in paths:
        source.update(path.relative_to(ROOT).as_posix().encode()+b'\0'+path.read_bytes())
    report = {'status': 'running', 'evidence_kind': 'synthetic_load', 'platform': platform.platform(),
              'python': sys.version, 'code_and_rules_sha256': source.hexdigest(), 'cases': [],
              'limitations': ['In-process admission and sequential drain, not HTTPS/network throughput.',
                             'Synthetic behavior mix; no live endpoints or malware efficacy measurement.',
                             'RSS sampled after each event; may miss peaks. CPU seconds include duplicate retries.',
                             'Short local runs do not establish sustained capacity, maximum agents or HA.']}
    try:
        for count, hosts, batch in ((300, 1, 25), (1000, 4, 50), (2000, 8, 100)):
            with tempfile.TemporaryDirectory(prefix='behedr-phase8-load-') as directory:
                output = Path(directory)/'result.json'
                env = {**os.environ, 'EDR_ENV': 'test', 'EDR_JWT_SECRET': 'isolated-load-only-'+'z'*64,
                       'EDR_DATA_DIR': directory, 'EDR_BACKGROUND': 'false', 'EDR_MAX_PENDING_EVENTS': '100000',
                       'EDR_MIN_FREE_BYTES': '0', 'EDR_MAX_DATABASE_BYTES': '1073741824', 'EDR_EXPERIMENTAL_ML': 'false'}
                result = subprocess.run([sys.executable, __file__, '--worker', '--events', str(count),
                                         '--hosts', str(hosts), '--batch', str(batch), '--output', str(output)],
                                        env=env, capture_output=True, text=True, timeout=300)
                if result.returncode:
                    raise RuntimeError(result.stderr[-2000:])
                report['cases'].append(json.loads(output.read_text()))
                args.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
                print(f'{count} events / {hosts} simulated hosts: passed', flush=True)
        report['status'] = 'completed'
    except Exception as exc:
        report.update(status='failed', error=str(exc))
        raise
    finally:
        args.output.write_text(json.dumps(report, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
