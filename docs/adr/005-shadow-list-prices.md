# Separate public usage from shadow prices

Date: 2026-11-01. Status: accepted.

## Context and decision

Measure public jobs and committed ledgers, then apply the matching public paid equivalent. Preserve unknown price matches and missing sources. Label the result as a shadow estimate, with the source URL and retrieval date.

## Alternatives and consequences

Rejected: calling a free-tier charge zero usage, or multiplying storage inventory by a month without a measured duration. Credits, tax, negotiated rates and free tiers can change cash paid without changing measured consumption.

## Evidence

Read the corresponding method in packages/, evaluation/v2/plan.json, and the generated report in docs/methods/. Changes to this decision must preserve earlier registrations and promoted evidence.
