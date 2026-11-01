---
name: add-a-price-source
description: Add or update a public pricing source in MLSpend, including a provider fetch, normalization, provenance and lock promotion.
---

# Add A Price Source

Read AGENTS.md and packages/prices/book.py. Write a committed fetch request with exact SKU, region, unit, currency and term. Fetch in Actions with bounded retries and preserved raw bytes. Normalize Decimal rates without changing billed units; keep unavailable prices unknown. Record URL, retrieval date, raw SHA-256, effective date and source kind. Test a valid response, a malformed or mismatched unit response, and an empty response. Promote through a versioned lock and preserve prior evidence. Run price-lock and reconciliation checks. Rebuild derived claims only after the source is reviewed; never edit the locked book by hand.
