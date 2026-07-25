# Dataset Sources & Download Log

> This file is cited in `ml/reports/evaluation_report.md` as the dataset provenance record.

## PhishTank (Phishing URLs — Label: 1)

- **Source URL:** http://data.phishtank.com/data/online-valid.csv
- **Download Date:** _(fill in when downloaded)_
- **Row Count:** _(fill in after download)_
- **Description:** Verified active phishing URLs submitted by the community and validated by PhishTank. Only "online" and "verified" entries included.

## Tranco Top-1M (Legitimate Domains — Label: 0)

- **Source URL:** https://tranco-list.eu/download/AAAA/full
- **List Date:** _(fill in the list date shown on tranco-list.eu)_
- **Row Count (sampled):** _(fill in)_
- **Description:** Research-focused top-1M domain ranking. Domains converted to `https://<domain>` for the dataset.

## Known Limitations

- PhishTank URLs reflect phishing activity at download time. Novel phishing patterns not in this snapshot may not be represented.
- Tranco legitimate domains include only popular sites — the model may not generalize to obscure-but-legitimate low-traffic domains.
- Class balance was _(fill in)_ phishing / _(fill in)_ legitimate.
# Dataset Sources

## PhishTank
Source: http://data.phishtank.com/data/online-valid.csv
Download Date: 25 July 2026
Rows: 10000

## Tranco
Source: https://tranco-list.eu/download/AAAA/full
Download Date: 25 July 2026
Rows: 10000
