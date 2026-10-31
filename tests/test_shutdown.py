import threading


def test_worker_finishes_current_item_before_shutdown(monkeypatch):
    from server import ingestion
    entered = threading.Event()
    release = threading.Event()
    finished = threading.Event()

    def process():
        entered.set()
        release.wait(5)
        finished.set()
        return True

    monkeypatch.setattr(ingestion, 'process_one', process)
    ingestion.start_worker()
    try:
        assert entered.wait(2)
        assert not ingestion.stop_worker(timeout=0.01)
        release.set()
        assert ingestion.stop_worker(timeout=2)
        assert finished.is_set()
    finally:
        release.set()
        ingestion.stop_worker(timeout=2)
