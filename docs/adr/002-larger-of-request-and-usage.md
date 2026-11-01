# Charge the larger of request and usage

Date: 2026-11-01. Status: accepted.

## Context and decision

A reservation consumes scheduling capacity even when utilization is low. A burst can exceed its reservation and consume extra capacity. Attribute the larger value at each hour, retaining both raw signals.

## Alternatives and consequences

Rejected: usage-only, which rewards large idle reservations; request-only, which misses bursts. This can charge short bursts more than a monthly-average policy, so show that assumption.

## Evidence

Read the corresponding method in packages/, evaluation/v2/plan.json, and the generated report in docs/methods/. Changes to this decision must preserve earlier registrations and promoted evidence.
