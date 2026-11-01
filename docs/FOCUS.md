# FOCUS validation

The exporter uses the released FOCUS 1.4 CostAndUsage and ContractCommitment column definitions. `config/focus/1.4-columns.json` records the upstream specification commit and its column-level presence, type and nullability rules. Project tests additionally enforce the new applicability object and continuous-contract constraints.

The official `focus-validator` release 2.2.1 advertises remote rules for 1.4. On this build it fails before reading data because the released rule graph contains a dependency cycle between CommitmentDiscountUnit and CommitmentDiscountQuantity. The unmodified failure is recorded in [the Actions run](https://github.com/mekala27-45/mlspend/actions/runs/41260502906). No rule is deleted or weakened to manufacture a pass.

The integration therefore runs the newest usable prior ruleset, 1.3.0.1, in a separate environment. The local FOCUS 1.4 checks complement that result. A successful prior-version report is not represented as complete official 1.4 certification. The official XML reports are inspected for failures because the upstream CLI does not reliably signal data-rule failures through its exit status.

Every full export must be validated, including allocated charges. A two-hour development fixture checks integration quickly; it is not evidence that the full-year exports passed. Dataset-level validation status belongs in the generated manifest.

The allocation method `mlspend-usage-v2` uses each team's monthly usage weight divided by the total weight, with equal shares only when the total is zero. Its `UsageUnit` label is `Usage Share`, a dimensionless component of that documented method. It is not a physical CPU or GPU unit. The optional `UsageQuantity` is omitted; `AllocatedRatio` carries the normalized share. The label follows the official formatter's space-separated count-name syntax. The fast official fixture includes allocated rows so allocation metadata is checked before a full-year rebuild.
