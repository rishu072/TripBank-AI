import time
from collections import defaultdict, deque

from fastapi import Request

from .errors import AppError

hits = defaultdict(deque)


def limiter(name: str, limit: int, window: int):
    def dep(request: Request):
        who = request.client.host if request.client else "unknown"
        q = hits[f"{name}:{who}"]
        t = time.time()
        while q and q[0] < t - window:
            q.popleft()
        if len(q) >= limit:
            raise AppError("RATE_LIMITED", "Too many requests. Try again shortly.", 429)
        q.append(t)

    return dep
