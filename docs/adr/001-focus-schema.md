# Use FOCUS for the exchange format

Date: 2026-11-01. Status: accepted.

## Context and decision

A proprietary cost table would make ingestion simpler but hide purchase-versus-effective-cost semantics and force every downstream tool to learn our names. Use the current FOCUS datasets at the export boundary, with explicit extensions for synthetic provenance. Keep integer microdollars internally.

## Alternatives and consequences

Rejected: a homemade invoice schema; it would not exercise a portable cost contract. Accepted cost: more typed columns and supplemental validation while official rules have defects.

## Evidence

Read the corresponding method in packages/, evaluation/v2/plan.json, and the generated report in docs/methods/. Changes to this decision must preserve earlier registrations and promoted evidence.
