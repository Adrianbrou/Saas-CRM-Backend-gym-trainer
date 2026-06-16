"""
test_rate_limit.py - proves the login endpoint is rate limited.

Rate limiting is disabled globally in conftest (so the many logins in the rest of the suite
do not trip it). This test re-enables it for its own scope and confirms that the 6th login
within the window is rejected with 429 Too Many Requests.
"""


def test_login_is_rate_limited(client):
    from app.core.rate_limit import limiter

    limiter.enabled = True
    try:
        statuses = [
            client.post(
                "/auth/login",
                data={"username": "nobody@test.com", "password": "wrong"},
            ).status_code
            for _ in range(6)
        ]
        # Limit is 5/minute per IP: the first requests reach the endpoint (401 bad
        # credentials); the 6th is blocked by the limiter before the body runs.
        assert statuses[-1] == 429
        assert 401 in statuses
    finally:
        limiter.enabled = False
