"""
rate_limit.py — Shared slowapi Limiter instance.
Lives outside main.py so routers can apply @limiter.limit(...) without a circular import
(main.py imports the routers; a router importing back from main.py would cycle).
"""

import os

from slowapi import Limiter
from slowapi.util import get_remote_address

# Keyed by remote address — there's no real authenticated identity to key on yet (see
# LIMITATIONS.md); client_id is self-asserted and not verified, so it isn't trustworthy as a
# rate-limit key either.
#
# ESA_DISABLE_RATE_LIMIT gates the limiter off entirely, same pattern as ESA_ALLOW_FALLBACK
# (ADR-016): the e2e CI job runs two parallel Playwright workers that legitimately seed several
# scans each, all from the single GitHub Actions runner IP — a limit sized for distinct real
# users, not concurrent test workers sharing one address. The 10/minute limit itself is unchanged
# for every other environment, including local development; tests/integration/test_rate_limiting.py
# still runs against it directly and doesn't set this variable.
limiter = Limiter(
    key_func=get_remote_address,
    enabled=os.getenv("ESA_DISABLE_RATE_LIMIT") != "1",
)
