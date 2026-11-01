# Expose idle before distributing it

Date: 2026-11-01. Status: accepted.

## Context and decision

The asset cost first separates workload consumption from unused paid capacity. The statement then distributes idle and shared services using the selected policy while retaining the original idle line.

## Alternatives and consequences

Rejected: hiding idle inside every prediction without a separate line. That obscures the difference between an expensive workload and an oversized shared cluster.

## Evidence

Read the corresponding method in packages/, evaluation/v2/plan.json, and the generated report in docs/methods/. Changes to this decision must preserve earlier registrations and promoted evidence.
