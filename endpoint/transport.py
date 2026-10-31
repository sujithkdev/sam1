"""One bounded delivery cycle. No acknowledgment means no queue deletion."""
import time
import requests


class Sender:
    def __init__(self, spool, base, headers, verify=True, timeout=5, post=None):
        self.spool, self.base, self.headers = spool, base, headers
        self.verify, self.timeout, self.post = verify, timeout, post or requests.post
        self._last_path = None

    def record(self, state, **fields):
        previous = self.spool.source_state('transport')
        previous.update(state=state, observed_at=time.time(), **fields)
        self.spool.commit_source('transport', previous)
        return state

    def send(self, path, batch):
        self.record('sending', route=path, last_attempt_at=time.time(), batch_size=len(batch), http_status=None)
        try:
            response = self.post(self.base+path, json={'events':batch}, headers=self.headers,
                                 timeout=self.timeout, verify=self.verify, allow_redirects=False)
            status = response.status_code
            if status == 200:
                data = response.json()
                accepted = data.get('accepted') if isinstance(data, dict) else None
                sent = {e['event_id'] for e in batch}
                if not isinstance(accepted, list) or any(not isinstance(i, str) for i in accepted) or not set(accepted) <= sent:
                    return self.record('invalid_acknowledgment', http_status=status)
                ids = set(accepted)
                if not ids:
                    return self.record('no_acknowledgment', http_status=status)
                self.spool.acknowledge(ids)
                return self.record('acknowledged' if ids == sent else 'partial_acknowledgment',
                                   http_status=status, last_ack_at=time.time(), last_ack_count=len(ids))
            if status in (400, 413, 422):
                if len(batch) > 1:
                    for event in batch:
                        outcome = self.send(path, [event])
                        if outcome not in ('acknowledged', 'rejected'):
                            return outcome
                    return self.record('batch_isolated', http_status=status)
                # Do not retain arbitrary server response bodies (may contain secrets).
                self.spool.reject([batch[0]['event_id']], f'HTTP {status}: invalid telemetry; inspect server validation logs')
                return self.record('rejected', http_status=status)
            return self.record('authentication_rejected' if status in (401, 403) else
                               'server_backpressure' if status in (429, 503) else 'http_error', http_status=status)
        except requests.exceptions.SSLError:
            return self.record('tls_error')
        except requests.exceptions.ConnectTimeout:
            return self.record('connect_timeout')
        except requests.exceptions.ReadTimeout:
            return self.record('response_timeout')
        except requests.exceptions.Timeout:
            return self.record('timeout')
        except requests.exceptions.ConnectionError:
            return self.record('connection_error')
        except requests.RequestException:
            return self.record('request_error')
        except ValueError:
            return self.record('invalid_acknowledgment')

    def cycle(self):
        path, batch = self.spool.peek(after_path=self._last_path)
        self._last_path = path
        return self.send(path, batch) if batch else 'idle'
