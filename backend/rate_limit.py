"""
rate_limit.py — Shared slowapi Limiter instance.
Lives outside main.py so routers can apply @limiter.limit(...) without a circular import
(main.py imports the routers; a router importing back from main.py would cycle).
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Keyed by remote address — there's no real authenticated identity to key on yet (see
# LIMITATIONS.md); client_id is self-asserted and not verified, so it isn't trustworthy as a
# rate-limit key either.
limiter = Limiter(key_func=get_remote_address)
