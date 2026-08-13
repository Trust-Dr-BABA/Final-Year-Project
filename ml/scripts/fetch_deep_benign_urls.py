"""
fetch_deep_benign_urls.py — Sources genuinely path-bearing benign URLs by crawling Tranco domains.

Why this exists: the obvious benign sources — Tranco domains prefixed with a scheme, and PhiUSIIL's
"legitimate" class — both turned out to be bare domains with zero path presence when audited (see
ml/reports/leakage_audit_before.md). Training on either would relocate defect D1 rather than fix it.
Querying Common Crawl's index server was tried first and abandoned: it rate-limits aggressively and,
combined with a threaded retry loop, produced a run that hung for 50 minutes on 301 domains.

This is the fallback the project roadmap already anticipated: fetch each domain's homepage directly
and collect its real internal links. It is slower per domain than an index lookup would be in
principle, but it is fully self-directed — no third-party rate limit, no dependency on another
service's reliability — and every request is wrapped in a hard `asyncio.wait_for` ceiling, so one
unresponsive server can never stall the run by more than that ceiling.

Usage:
    python ml/scripts/fetch_deep_benign_urls.py --start-rank 200 --end-rank 8000 \
        --target-rows 9000 --out ml/data/raw/deep_benign_train.csv
    python ml/scripts/fetch_deep_benign_urls.py --start-rank 8001 --end-rank 14000 \
        --target-rows 1500 --out ml/data/raw/deep_benign_holdout.csv
"""

import argparse
import asyncio
import csv
import logging
import random
import re
import sys
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
import tldextract

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
TRANCO_TOP1M = RAW_DIR / "tranco_top1m" / "top-1m.csv"

# Hard ceiling per domain, enforced independently of whatever timeout httpx itself applies. This is
# the fix for the Common Crawl attempt, where a stuck connection blocked its worker indefinitely.
PER_DOMAIN_DEADLINE = 8.0

SKIP_EXTENSIONS = (
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico", ".css", ".js", ".woff",
    ".woff2", ".ttf", ".mp4", ".mp3", ".pdf", ".zip", ".xml", ".json", ".txt", ".map",
)
HREF_RE = re.compile(r'href\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)


# Minimal href collector — avoids adding a new HTML-parsing dependency for a one-off extraction.
class LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        for name, value in attrs:
            if name == "href" and value:
                self.hrefs.append(value)


# Load (rank, domain) pairs from the ranked Tranco list within a rank range.
def load_domains(start_rank: int, end_rank: int) -> list[tuple[int, str]]:
    domains = []
    with open(TRANCO_TOP1M, newline="", encoding="utf-8") as handle:
        for row in csv.reader(handle):
            rank = int(row[0])
            if start_rank <= rank <= end_rank:
                domains.append((rank, row[1]))
    return domains


# True if a URL's path is a real page rather than an asset or the bare root.
def is_worth_keeping(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    path = parsed.path.strip("/")
    if not path or "#" in url:
        return False
    if path.lower().endswith(SKIP_EXTENSIONS):
        return False
    if len(url) > 300 or len(url) < 15:
        return False
    return True


# Registrable domain (eTLD+1), so subdomain links still count as "internal" but cross-site ones don't.
def registrable(hostname: str) -> str:
    ext = tldextract.extract(hostname or "")
    return f"{ext.domain}.{ext.suffix}" if ext.suffix else hostname


# Fetch one domain's homepage and extract up to `cap` real internal links with non-trivial paths.
async def fetch_domain_links(client: httpx.AsyncClient, domain: str, cap: int) -> list[str]:
    home = f"https://{domain}/"
    try:
        response = await client.get(home, follow_redirects=True)
    except httpx.HTTPError:
        try:
            response = await client.get(f"http://{domain}/", follow_redirects=True)
        except httpx.HTTPError:
            return []

    if response.status_code != 200:
        return []
    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type:
        return []

    base = str(response.url)
    base_registrable = registrable(urlparse(base).hostname or domain)

    parser = LinkCollector()
    try:
        parser.feed(response.text[:200_000])  # cap parse size; homepages don't need more
    except Exception:  # noqa: BLE001 — malformed HTML must not abort the crawl
        return []

    found: list[str] = []
    seen: set[str] = set()
    for href in parser.hrefs:
        absolute = urljoin(base, href)
        if absolute in seen:
            continue
        if not is_worth_keeping(absolute):
            continue
        if registrable(urlparse(absolute).hostname or "") != base_registrable:
            continue
        seen.add(absolute)
        found.append(absolute)
        if len(found) >= cap:
            break
    return found


# Fetch with a hard deadline so one unresponsive domain can never stall the whole run.
async def fetch_with_deadline(client: httpx.AsyncClient, domain: str, cap: int) -> list[str]:
    try:
        return await asyncio.wait_for(fetch_domain_links(client, domain, cap), timeout=PER_DOMAIN_DEADLINE)
    except (asyncio.TimeoutError, Exception):  # noqa: BLE001 — one bad domain must not abort the run
        return []


# Crawl a rank range concurrently, stopping once the target row count is reached.
async def run(start_rank: int, end_rank: int, target_rows: int, cap: int,
              concurrency: int, out: Path) -> None:
    domains = load_domains(start_rank, end_rank)
    random.Random(42).shuffle(domains)
    logger.info(
        "Crawling up to %d domains (rank %d-%d) for %d benign URLs, cap %d/domain, concurrency %d",
        len(domains), start_rank, end_rank, target_rows, cap, concurrency,
    )

    limits = httpx.Limits(max_connections=concurrency, max_keepalive_connections=concurrency)
    timeout = httpx.Timeout(connect=4.0, read=5.0, write=4.0, pool=4.0)
    semaphore = asyncio.Semaphore(concurrency)

    rows: list[tuple[int, str, str]] = []
    queried = 0
    start = time.monotonic()
    stop = asyncio.Event()

    async def worker(rank: int, domain: str, client: httpx.AsyncClient) -> None:
        nonlocal queried
        if stop.is_set():
            return
        async with semaphore:
            if stop.is_set():
                return
            urls = await fetch_with_deadline(client, domain, cap)
        queried += 1
        for url in urls:
            rows.append((rank, domain, url))
        if queried % 250 == 0:
            elapsed = time.monotonic() - start
            rate = queried / elapsed * 60
            logger.info(
                "%d/%d domains queried, %d URLs collected, %.0fs elapsed (%.0f domains/min)",
                queried, len(domains), len(rows), elapsed, rate,
            )
        if len(rows) >= target_rows:
            stop.set()

    headers = {"User-Agent": "Mozilla/5.0 (research corpus builder; contact via repository)"}
    async with httpx.AsyncClient(limits=limits, timeout=timeout, headers=headers) as client:
        tasks = [asyncio.create_task(worker(rank, domain, client)) for rank, domain in domains]
        for task in asyncio.as_completed(tasks):
            await task
            if stop.is_set():
                break
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    elapsed = time.monotonic() - start
    rows.sort(key=lambda r: r[0])
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["rank", "domain", "url"])
        writer.writerows(rows[:target_rows])

    logger.info(
        "Done in %.0fs. Wrote %d benign URLs from %d/%d domains queried to %s",
        elapsed, min(len(rows), target_rows), queried, len(domains), out,
    )
    if len(rows) < target_rows:
        logger.warning(
            "Only reached %d/%d target rows — widen --end-rank or raise --cap.",
            len(rows), target_rows,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-rank", type=int, required=True)
    parser.add_argument("--end-rank", type=int, required=True)
    parser.add_argument("--target-rows", type=int, required=True)
    parser.add_argument("--cap", type=int, default=4, help="max URLs kept per domain")
    parser.add_argument("--concurrency", type=int, default=40)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    if not TRANCO_TOP1M.exists():
        logger.error("Ranked Tranco list not found at %s", TRANCO_TOP1M)
        sys.exit(2)

    asyncio.run(run(args.start_rank, args.end_rank, args.target_rows, args.cap,
                    args.concurrency, args.out))


if __name__ == "__main__":
    main()
