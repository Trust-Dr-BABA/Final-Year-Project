import os


os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test"
)
# No trained model is committed to the repo, so tests exercise the heuristic fallback (ADR-016
# gates it behind this flag in serving deployments, but development/test keeps it on by default).
os.environ.setdefault("ESA_ALLOW_FALLBACK", "1")
