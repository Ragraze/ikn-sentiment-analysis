"""Bound inference work and encode spreadsheet exports."""
from collections import deque
import math
import threading
import time
import unicodedata
from urllib.parse import urlsplit


class RequestBudget:
    def __init__(self, limit=30, window=60):
        if type(limit) is not int or limit < 1 or window <= 0:
            raise ValueError('Batas request dan jendela waktu harus positif.')
        self.limit = limit
        self.window = window
        self._requests = deque()
        self._lock = threading.Lock()

    def retry_after(self):
        with self._lock:
            now = time.monotonic()
            while self._requests and self._requests[0] <= now - self.window:
                self._requests.popleft()
            if len(self._requests) >= self.limit:
                return max(1, math.ceil(self.window - (now - self._requests[0])))
            self._requests.append(now)
            return 0


def origin_of(url):
    try:
        parsed = urlsplit(url)
        if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
            return None
        if parsed.path not in ('', '/') or parsed.query or parsed.fragment:
            return None
        return parsed.scheme, parsed.hostname.lower(), parsed.port or (443 if parsed.scheme == 'https' else 80)
    except (ValueError, AttributeError):
        return None


def spreadsheet_text(value):
    normalized = unicodedata.normalize('NFKC', value).lstrip('\ufeff\u200b\u200c\u200d \t\r\n')
    if value.startswith(('\t', '\r', '\n')) or normalized.startswith(('=', '+', '-', '@')):
        return "'" + value
    return value
