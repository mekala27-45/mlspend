# Fetch sources in Actions and preserve locks

Date: 2026-11-01. Status: accepted.

## Context and decision

Actions has a repeatable network environment and creates an attributable source artifact. Record requests, raw response hashes, frozen repository commits and normalized values before promotion. Rebuild calculations from those locks without silently fetching new prices.

## Alternatives and consequences

Rejected: laptop-only screenshots, undocumented manual rates, and automatic refresh during a scientific rebuild. The local environment blocks network access, but that is also a reason to make source acquisition explicit rather than bypass provenance.

## Evidence

Read the corresponding method in packages/, evaluation/v2/plan.json, and the generated report in docs/methods/. Changes to this decision must preserve earlier registrations and promoted evidence.
