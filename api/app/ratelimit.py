"""In-memory token bucket per client. Enough for a single API instance."""
import hmac
import threading
import time

from fastapi import Request


class TokenBucket:
    def __init__(self, per_minute: int, burst: int, max_clients: int = 50_000):
        if per_minute <= 0 or burst < 1:
            raise ValueError("rate limit needs per_minute > 0 and burst >= 1")
        self.rate = per_minute / 60.0
        self.burst = burst
        self.max_clients = max_clients
        self.state: dict[str, tuple[float, float]] = {}
        self.lock = threading.Lock()

    def allow(self, key: str) -> tuple[bool, float]:
        """Returns (allowed, seconds until the next token)."""
        now = time.monotonic()
        with self.lock:
            if len(self.state) >= self.max_clients:
                # drop clients idle for over ten minutes; if that is not enough,
                # drop the least recently seen half so memory stays bounded
                self.state = {k: v for k, v in self.state.items() if now - v[1] < 600}
                if len(self.state) >= self.max_clients:
                    keep = sorted(self.state.items(), key=lambda kv: kv[1][1])[len(self.state) // 2:]
                    self.state = dict(keep)
            tokens, last = self.state.get(key, (float(self.burst), now))
            tokens = min(self.burst, tokens + (now - last) * self.rate)
            if tokens < 1:
                self.state[key] = (tokens, now)
                return False, (1 - tokens) / self.rate
            self.state[key] = (tokens - 1, now)
            return True, 0.0


def client_key(request: Request, proxy_key: str, trust_forwarded_for: bool) -> str | None:
    """Who to rate limit. A forwarded visitor IP is only believed when the
    caller proves it is our own web server by sending the shared proxy key.
    Returns None for the web server's own cached page renders (key, no visitor),
    which are not limited."""
    sent = request.headers.get("x-proxy-key", "")
    if proxy_key and sent and hmac.compare_digest(sent, proxy_key):
        visitor = request.headers.get("x-client-ip", "").strip()
        return f"v:{visitor[:64]}" if visitor else None
    if trust_forwarded_for:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            return f"f:{forwarded.split(',')[0].strip()[:64]}"
    return f"c:{request.client.host if request.client else 'unknown'}"
