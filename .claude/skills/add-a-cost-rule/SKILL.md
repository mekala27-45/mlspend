---
name: add-a-cost-rule
description: Add an allocation, ownership or waste rule to MLSpend and evaluate its accounting invariants against independent truth.
---

# Add A Cost Rule

Read AGENTS.md, evaluation/v2/plan.json and the relevant method module. Consume observed telemetry or contracted marts only; never import sealed truth into a method. State the economic assumption and the counterfactual action. Add tests for a valid nontrivial case, an invariant-violating case and empty input. Preserve exact money totals and unknown denominators. Register a new study version before changing thresholds after holdout results are known. Have packages/evaluation grade the rule with independent reruns, report boundary failures and uncertainty, and regenerate claims from the manifest. Run the import-boundary gate and affected tests.
