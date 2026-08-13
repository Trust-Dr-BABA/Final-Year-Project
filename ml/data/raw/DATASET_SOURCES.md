# Dataset Sources & Download Log

> Cited in `ml/reports/evaluation_report.md` §Dataset provenance and in the thesis, Appendix B.

## PhishTank (phishing class, label = 1)

- **Source:** http://data.phishtank.com/data/online-valid.csv
- **Download date:** 25 July 2026
- **Rows:** 10,000
- **Columns retained:** `url`, `submission_time`, `verified`, `target`
- **Filter applied:** `verified == "yes"` (10,000 / 10,000 rows passed — the download already
  contains only verified entries)
- **Description:** Community-submitted, PhishTank-verified phishing URLs. `submission_time` is
  retained specifically to enable the temporal train/test split (Sprint 2); an earlier version of
  this pipeline discarded every column except `url`, which made that split impossible. `target`
  (the impersonated brand, where known) is retained as ground truth for evaluating
  `brand_impersonation` independently of the feature extractor that also produces it.

## Benign class, label = 0 — three sources tried, two rejected

**What was tried first, and why it failed.** The obvious benign source is a domain popularity
ranking: take the top N Tranco domains and prefix `https://`. This was the original approach, and
it produces bare domains with no path — `https://example.com`, never `https://example.com/anything`.
Every phishing URL in the same corpus carries a path. The classifier's job stopped being "detect
phishing" and became "detect the presence of a path," which is defect D1
(`ml/reports/leakage_audit_before.md`: `url_entropy` alone reaches 0.9001 standalone AUC; benign
path presence 0.0% against phishing's 65.2%).

The obvious fix — swap in a different published dataset — was tried next and also failed, for the
same underlying reason. **PhiUSIIL** (UCI ML Repository, ID 967) is a well-cited URL-level phishing
dataset with a "legitimate" class of 134,850 rows. Audited the same way, its legitimate class is
*also* 0% path presence: `https://www.ringling.org`, `https://www.hlcommission.org`, never a page
beneath the root. Its legitimate URLs are, structurally, the same shape as Tranco's — both are
domain-ranking-derived. Using it would have relocated D1, not fixed it.

**What was used instead.** `ml/scripts/fetch_deep_benign_urls.py` crawls the homepage of each
domain in a Tranco-ranked range directly and extracts real internal same-domain links — genuine
deep pages: `https://substack.com/@jameelajamil/note/...`, `https://arxiv.org/search`,
`https://www.scribd.com/docs/Biography-Memoir`. This is slower to produce than downloading a
published file, but it is the only one of the three approaches that actually yields path-bearing
benign URLs, which is the one property the corpus needs.

An index-based alternative — querying Common Crawl's CDX index server by domain, which would have
avoided crawling altogether — was attempted first and abandoned. It rate-limits aggressively under
concurrent access and a threaded retry loop against it hung for 50 minutes with no output. The
direct-crawl approach replaced it, using `asyncio` with a hard per-domain deadline
(`asyncio.wait_for`, 8 s) specifically so that no single unresponsive server can stall the run —
the failure mode that ended the Common Crawl attempt.

- **Source:** live crawl of domain homepages, domains drawn from the Tranco ranked list. The list
  itself is not committed (22 MB, trivially reproducible) — fetch it with:
  ```
  curl -sL -o ml/data/raw/tranco_top1m.csv.zip https://tranco-list.eu/top-1m.csv.zip
  unzip -o ml/data/raw/tranco_top1m.csv.zip -d ml/data/raw/tranco_top1m
  ```
  List dated 12 August 2026 (per its HTTP `Last-Modified` header at download time).
- **Crawl date:** 13 August 2026
- **Training pool:** domains ranked 200–20,000 (below rank 200 to exclude CDN/infrastructure
  domains — `cloudflare.com`, `gstatic.com` — that are not sites a user browses)
- **Method:** fetch each domain's homepage (`https://{domain}/`, HTTP fallback on failure);
  extract `<a href>` targets; keep same-registrable-domain links with a non-trivial path, excluding
  static assets (images, stylesheets, scripts, fonts) and fragment-only anchors; keep up to 4
  links per domain to bound any single site's influence on the corpus
- **Rows collected:** 9,000 deep-path URLs from 5,288 domains (476 s at ~700 domains/min,
  `ml/data/raw/deep_benign_train.csv`)
- **Path-presence mixing:** every crawled row has a path by construction, which on its own would
  just move defect D1 rather than fix it (a 100%-path-bearing benign class is exactly as
  structurally artificial as a 0%-path-bearing one). `prepare_dataset.py` measures the *phishing*
  class's own path-presence rate (65.2%) and adds bare-homepage rows for a matching fraction of
  benign domains, so the benign class's path structure is calibrated to the other class's
  naturally-observed rate rather than fixed at either extreme.

## False-positive evaluation holdout

- **Source:** the same crawl method, domains ranked 20,001–40,000 — **disjoint from the training
  range**, so no domain contributes to both training and evaluation
- **Purpose:** answers "does this flag popular sites it has never seen," which is the single most
  persuasive correctness measure for a browser extension. A held-out slice of the *same*
  construction as the training data is a stronger test of this than reusing Tranco bare domains
  would have been, since it tests exactly the kind of URL (real, deep-path, popular-site) the
  extension will actually encounter.
- **Rows collected:** 1,500 deep-path URLs from 806 domains (49 s), deduplicated to 1,488
  (`ml/data/processed/fp_holdout.csv`)

## Known limitations

- PhishTank reflects phishing activity current at download time; campaigns that emerged afterward
  are absent, which is precisely why the temporal split (train on the earlier submission window,
  test on the later one) is the primary evaluation protocol rather than a random split.
- The benign crawl only reaches domains whose homepage returns static, parseable `<a href>` links
  within an 8-second budget. Heavily JavaScript-rendered homepages (which don't expose links in
  the initial HTML) are under-represented as a result — a genuine gap in corpus diversity, recorded
  in the thesis limitations section.
- Benign URLs carry no submission timestamp (a crawl date is not a publication date), so the
  temporal split is applied to the phishing class only; the benign class is split by simple random
  sampling in matching proportion. This is stated explicitly rather than implied, since it is a
  real asymmetry in how the two classes were split.
- Class balance and final row counts are logged by `prepare_dataset.py` on each run rather than
  hand-copied here, so this file cannot drift out of sync with the data it describes.
