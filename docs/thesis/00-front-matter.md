# Explainable Multi-Signal Phishing and Privacy Detection in the Browser

**A Final Year Project Report**

---

*[TITLE PAGE — complete these fields to your department's template]*

| | |
|---|---|
| **Title** | Explainable Multi-Signal Phishing and Privacy Detection in the Browser |
| **Author** | *[full name]* |
| **Student number** | *[number]* |
| **Degree** | *[BSc/BEng … in …]* |
| **Department** | *[department]* |
| **Institution** | *[institution]* |
| **Supervisor** | *[name]* |
| **Submission date** | *[date]* |


# Declaration

I declare that this report is my own work, that it has not been submitted for any other academic
award, and that all sources of information have been acknowledged in the text and listed in the
references.

Signed: ______________________  Date: ______________


# Abstract

Phishing defences in the browser fall into two groups, and both withhold their reasoning. Blocklists
report that a page is blocked without saying why, and are silent on any page not yet listed.
Machine-learned classifiers report a probability, which is equally opaque to the person who has to
act on it. Both judge a page almost entirely on its URL string, ignoring behaviour the browser has
already observed — the third-party trackers a page contacted, the insecure resources it pulled into a
secure document, the redirects it passed through, the device permissions it demanded before the user
touched anything.

This project delivers a system that assesses pages on that wider evidence and explains every verdict
in plain English. A Chrome Manifest V3 extension instruments page loads without re-fetching the page
under assessment. A FastAPI service extracts lexical features, scores them with a gradient-boosted
classifier, and attributes the score with SHAP. Browser-observed signals are then fused into the
result as documented weights added in log-odds space.

The design rests on one observation. SHAP values for a tree ensemble are additive contributions in
log-odds, and a hand-set fusion weight added in the same space is the same kind of quantity.
Learned attributions and hand-set signal weights are therefore directly comparable, and can be
ranked in a single explanation, rendered by a single chart and stored in a single representation —
with no schema change anywhere downstream. This is what allows the system to be genuinely
multi-signal and genuinely explainable at once, rather than trading one against the other.

Evaluation is treated as a first-class deliverable. During development the training corpus was found
to be trivially separable for a reason unrelated to phishing: benign URLs were bare domains while
malicious URLs carried full paths, so URL length alone came close to solving the task. An audit
instrument was built to quantify this rather than merely remove it, and the resulting before-and-after
comparison is presented as a finding in its own right. Evaluation is specified under a temporal
split and an unseen-registrable-domain split, against five baselines including a blocklist, with
calibration measured and explanation faithfulness tested by ablation.

Software verification is complete: 25 automated tests pass, browser instrumentation is confirmed
against live commercial sites, and every failure path is confirmed to refuse rather than to fabricate
a verdict. Model measurement against the rebuilt corpus is outstanding and is itemised explicitly
rather than estimated.

**Keywords** — phishing detection, explainable artificial intelligence, SHAP, browser extension,
privacy analysis, dataset leakage, model calibration


# Acknowledgements

*[Add your acknowledgements here.]*


# Table of contents

```{=openxml}
<w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/></w:r><w:r><w:instrText xml:space="preserve"> TOC \o "1-3" \h \z \u </w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>Right-click here and choose "Update Field" to build the table of contents.</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>
```


# List of figures

| Figure | Title | Section |
|---|---|---|
| 1.1 | System context | 1.1 |
| 2.1 | System use case diagram | 2.5 |
| 2.2 | Domain (conceptual) model | 2.10 |
| 2.3 | System sequence diagram — UC-01 Analyse Visited Page | 2.8 |
| 2.4 | System sequence diagram — UC-02 View Verdict and Explanation | 2.8 |
| 2.5 | System sequence diagram — dashboard use cases | 2.8 |
| 2.6 | Activity diagram — end-to-end page analysis | 2.11 |
| 2.7 | Activity diagram — offline training pipeline | 2.11 |
| 2.8 | Sequence diagram — assessment operation | 2.12 |
| 2.9 | Communication diagram — assessment operation | 2.12 |
| 3.0 | Layered architecture and the attribution path | 3.1 |
| 3.1 | Class diagram | 3.3 |
| 3.2 | Logical entity-relationship model | 3.4.1 |
| 3.3 | Physical schema as implemented | 3.4.2 |
| 3.4 | Component diagram | 3.5 |
| 4.1 | Deployment diagram | 4.2 |

# List of tables

| Table | Title | Section |
|---|---|---|
| 3.1 | Design decision register | 3.2 |
| 5.1 | Pending measurement register | 5.2 |
| 5.2–5.5 | Dataset audit, original and rebuilt corpora | 5.4 |
| 5.6–5.8 | Unit test suite, cases and defect regressions | 5.5 |
| 5.9 | Integration test cases | 5.6 |
| 5.10 | System test cases | 5.7 |
| 5.11 | Corpus composition | 5.8 |
| 5.12–5.13 | Detection performance and confusion matrix | 5.9 |
| 5.14 | Baseline comparison | 5.10 |
| 5.15–5.16 | False positives and calibration | 5.11 |
| 5.17–5.18 | Faithfulness and weight sensitivity | 5.12 |
| 5.19 | Assessment latency | 5.13 |
| 5.20 | Security and privacy test cases | 5.14 |
| 5.21 | End-to-end result | 5.15 |
| 5.22 | Defect log | 5.16 |
| 6.1 | Objectives and outcomes | 6.2 |


# Abbreviations

| Term | Expansion |
|---|---|
| ADR | Architectural Decision Record |
| API | Application Programming Interface |
| APWG | Anti-Phishing Working Group |
| ASGI | Asynchronous Server Gateway Interface |
| AUC | Area Under the Curve |
| CI | Continuous Integration |
| DOM | Document Object Model |
| ECE | Expected Calibration Error |
| ERD | Entity-Relationship Diagram |
| eTLD+1 | Effective Top-Level Domain plus one label (the registrable domain) |
| F1 | Harmonic mean of precision and recall |
| JSONB | Binary JSON storage type in PostgreSQL |
| MV3 | Manifest Version 3 (Chrome extension platform) |
| ORM | Object-Relational Mapper |
| ROC | Receiver Operating Characteristic |
| SHAP | SHapley Additive exPlanations |
| SSD | System Sequence Diagram |
| TLD | Top-Level Domain |
| TTL | Time To Live |
| UML | Unified Modeling Language |
| UUID | Universally Unique Identifier |
| VT | VirusTotal |
| XAI | Explainable Artificial Intelligence |


# Identifier schemes

Items in this report are labelled with a prefix indicating what kind of item they are. All eleven
schemes are listed here so that any identifier encountered in the text can be resolved without
searching for its first use.

| Prefix | Meaning | Defined in | Example |
|---|---|---|---|
| **FR-nn** | Functional requirement | §2.2 | FR-02, tracker counting |
| **NFR-nn** | Non-functional requirement | §2.3 | NFR-01, latency budget |
| **UC-nn** | Use case | §2.6 | UC-01, Analyse Visited Page |
| **CO-nn** | Operation contract | §2.9 | CO-04, `pageLoadComplete` |
| **ADR-nnn** | Design decision record | §3.2 | ADR-014, log-odds fusion |
| **O-n** | Project objective | §1.3 | O5, the fusion objective |
| **C-n** | Project claim under test | §1.5 | C2, multi-signal detection |
| **D-n** | Defect found during development | §4.7 | D1, the corpus artefact |
| **TC-x-nn** | Test case, where *x* denotes the level | Ch. 5 | TC-U-17, unit; TC-I-05, integration; TC-S-06, system; TC-P, performance; TC-SEC, security; TC-M, maintainability |
| **B-n** | Evaluation baseline | §5.10 | B1, blocklist lookup |
| **⟨M-nn⟩** | Measurement not yet taken | Table 5.1 | ⟨M-07⟩, temporal-split F1 |

The three that matter most when reading Chapter 5 are **C-n** (what is being claimed), **⟨M-nn⟩**
(what has not yet been measured) and **D-n** (what went wrong and how it was found).


# Note on the presentation of results

This report distinguishes between figures that have been measured and figures that have not.

Measured values are stated plainly with the date and environment of the run that produced them.
Values not yet measured are marked **⟨M-nn⟩** and enumerated in Table 5.1. No quantitative result in
this document is estimated, interpolated, or carried over from an earlier configuration of the
system. Where a measurement is outstanding, the report says so rather than supplying a plausible
figure.

This convention is applied deliberately. Section 4.7.1 describes a corpus defect that produced an
excellent-looking score with no validity whatsoever, and the discipline adopted afterwards is the
direct response to it.
