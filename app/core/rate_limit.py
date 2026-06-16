"""
rate_limit.py - Request rate limiting (slowapi).

ONE shared Limiter, keyed by the client's IP address (get_remote_address). A route opts in
with the decorator `@limiter.limit("5/minute")`. slowapi counts requests per key per time
window; once the limit is exceeded it raises RateLimitExceeded, which the handler registered
in main.py turns into a 429 Too Many Requests - before the route body ever runs.

Why login especially: without a limit, POST /auth/login is brute-forceable - an attacker can
throw unlimited password guesses at it. A per-IP limit makes online guessing impractical.

Storage: in-memory by default, which is PER PROCESS. That is fine for a single instance or a
demo. Across multiple Fargate tasks each task would count separately, so for production I would
point it at Redis (which this app already runs) so the count is shared across every instance:

    limiter = Limiter(key_func=get_remote_address,
                      storage_uri="redis://<host>:6379")

The `enabled` flag is flipped off in the test suite (see tests/conftest.py) so the many logins
across tests do not trip the limit; one dedicated test re-enables it to prove the 429.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# key_func decides WHAT we count per: here, the caller's IP. Could also be a user id or API key.
limiter = Limiter(key_func=get_remote_address)
