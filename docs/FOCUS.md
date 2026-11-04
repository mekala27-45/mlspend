# FOCUS validation

The exporter uses the released FOCUS 1.4 CostAndUsage and ContractCommitment column definitions. `config/focus/1.4-columns.json` records the upstream specification commit and its column-level presence, type and nullability rules. Project tests additionally enforce the new applicability object and continuous-contract constraints.

The official `focus-validator` release 2.2.1 advertises remote rules for 1.4. On this build it fails before reading data because the released rule graph contains a dependency cycle between CommitmentDiscountUnit and CommitmentDiscountQuantity. The unmodified failure is recorded in [the Actions run](https://github.com/mekala27-45/mlspend/actions/runs/41260502906). No rule is deleted or weakened to manufacture a pass.

The integration therefore runs the newest usable prior ruleset, 1.3.0.1, in a separate environment. The local FOCUS 1.4 checks complement that result. A successful prior-version report is not represented as complete official 1.4 certification. The official XML reports are inspected for failures because the upstream CLI does not reliably signal data-rule failures through its exit status.

Every full export must be validated, including allocated charges. A two-hour development fixture checks integration quickly; it is not evidence that the full-year exports passed. Dataset-level validation status belongs in the generated manifest.

The allocation method `mlspend-usage-v2` uses each team's monthly usage weight divided by the total weight, with equal shares only when the total is zero. Its `UsageUnit` label is `Usage Share`, a dimensionless component of that documented method. It is not a physical CPU or GPU unit. The optional `UsageQuantity` is omitted; `AllocatedRatio` carries the normalized share. The label follows the official formatter's space-separated count-name syntax. The fast official fixture includes allocated rows so allocation metadata is checked before a full-year rebuild.

## Full-year evidence

[Run 41480417577](https://github.com/mekala27-45/mlspend/actions/runs/41480417577) completed successfully on November 2, 2026. It checked all 589,850 source rows, all 852,660 allocated rows and both commitments. Each cost export ran 764 official checks; the commitment dataset ran 114 with no failures. The same twelve documented upstream contradictions remain in each cost report, with zero unreviewed failures. Raw XML and summaries are preserved under `results/full-focus/`. This result complements the supplemental 1.4 contracts and does not imply official 1.4 certification.

Cross-file totals match exactly at USD 348535.007258 effective cost and USD 372415.671738 billed cost. Every origin allocation ratio sums to one within absolute tolerance 1e-12. [Release candidate build 41477467691](https://github.com/mekala27-45/mlspend/actions/runs/41477467691) reproduced the same manifest in the primary checkout and a detached worktree under two independent hash seeds, and passed LibreOffice recalculation. The earlier full checks remain available in runs 41326225853 and 41327002636.
