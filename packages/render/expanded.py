"""Render public claims from the registered study and measured public sources."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from packages.core.io import ROOT, STATEMENT, canonical, digest, read_json


def money(value: float | int | None, micro: bool = True) -> str:
    return "Not measured" if value is None else f"${value / (1000000 if micro else 1):,.2f}"


def percent(value: float | None) -> str:
    return "Not measured" if value is None else f"{value:.1%}"


def table(title: str, headers: list[str], rows: list[list[Any]], note: str = "") -> dict[str, Any]:
    return {"title": title, "headers": headers, "rows": rows, "note": note}


def page(title: str, intro: str, sections: list[dict[str, Any]], limit: str) -> dict[str, Any]:
    return {"title": title, "intro": intro, "sections": sections, "limit": limit}


def markdown(section: dict[str, Any]) -> str:
    def cell(value: Any) -> str:
        return (
            str(value if value is not None else "Not measured").replace("|", "/").replace("\n", " ")
        )

    rows = [section["headers"], ["---"] * len(section["headers"]), *section["rows"]]
    return (
        "\n\n## "
        + str(section["title"])
        + "\n\n"
        + str(section["note"])
        + "\n\n"
        + "\n".join("| " + " | ".join(map(cell, row)) + " |" for row in rows)
        + "\n"
    )


def render(root: Path = ROOT, check: bool = False) -> None:
    from packages.render.documents import _write_or_check

    m = read_json(root / "results/expanded/manifest.json")
    if m["mode"] != "full_year" or not m["allocation"]:
        raise ValueError("Public report requires the nonempty full study")
    original = read_json(root / "results/manifest.json")
    portfolio = original["portfolio"]
    ledger = read_json(root / "results/committed-ledgers.json")
    prices = read_json(root / "data/prices/expanded/book.json")["rows"]
    latest = max(row["month"] for row in m["allocation"])
    allocations = [row for row in m["allocation"] if row["month"] == latest]
    methods = ["even", "direct", "usage", "custom", "shapley"]
    d = m["detection"]
    actions = m["recommendations"]
    pages: dict[str, Any] = {}
    pages["statement"] = page(
        "Every dollar has an owner.",
        "A simulated ML platform at a locked public price snapshot. Usage is the allocation method of record. Idle capacity is visible before distribution.",
        [
            table(
                "The monthly statement · " + latest,
                ["Owner", "Direct", "Idle + shared", "Total"],
                [
                    [
                        r["team"],
                        money(r["direct_micro"]),
                        money(r["methods"]["usage"] - r["direct_micro"]),
                        money(r["methods"]["usage"]),
                    ]
                    for r in allocations
                ],
                "USD effective cost. Purchase cash and amortized consumption are reconciled separately.",
            ),
            table(
                "The calendar",
                ["Month", "Effective cost"],
                [[k, money(v)] for k, v in m["generation"]["monthly_micro"].items()],
            ),
        ],
        "This is a synthetic platform, not a provider invoice. Later public prices are applied to an earlier simulated calendar; credits, tax and negotiated discounts are excluded.",
    )
    pages["allocation"] = page(
        "The method changes the statement.",
        "The same source total supports five policies. The capacity Shapley calculation enumerates every coalition; its normalized shares allocate the recorded shared bill.",
        [
            table(
                "One total, five policies",
                ["Team", *methods],
                [[r["team"], *[money(r["methods"][k]) for k in methods]] for r in allocations],
            ),
            table(
                "Idle before allocation",
                ["Pool", "Asset cost", "Idle cost", "Idle share"],
                [
                    [
                        r["pool"],
                        money(r["asset_micro"]),
                        money(r["idle_micro"]),
                        percent(r["idle_share"]),
                    ]
                    for r in m["idle"]
                    if r["month"] == latest
                ],
            ),
            table(
                "Ownership inference",
                ["Population", "Correct", "Wrong", "Unresolved", "Precision", "Recall"],
                [
                    [
                        m["ownership"]["population"],
                        m["ownership"]["correct"],
                        m["ownership"]["wrong"],
                        m["ownership"]["unresolved"],
                        percent(m["ownership"]["precision"]),
                        percent(m["ownership"]["recall"]),
                    ]
                ],
            ),
            table(
                "Largest change across policies",
                ["Team", "Month", "Range"],
                [
                    [
                        m["largest_method_move"]["team"],
                        m["largest_method_move"]["month"],
                        money(m["largest_method_move"]["range_micro"]),
                    ]
                ],
            ),
        ],
        "Capacity contribution is a fairness reference under this coalition cost model. It is not an objective fairness label. Namespace and network must agree before an untagged charge is assigned.",
    )
    latest_units = [r for r in m["units"] if r["month"] == latest]
    pages["unit"] = page(
        "One prediction has two prices.",
        m["unit_policy"],
        [
            table(
                "Inference · USD per 1,000 predictions",
                ["Team", "Model version", "Outputs", "Average", "Next batch"],
                [
                    [
                        r["team"],
                        r["model"],
                        r["outputs"],
                        money(r["micro_per_1000_predictions"]),
                        money(r["marginal_micro_next_1000"]),
                    ]
                    for r in latest_units
                    if r["service"] == "inference"
                ],
            ),
            table(
                "Answers and training",
                ["Team", "Model", "Unit", "Completed", "Failures", "Fully loaded / output"],
                [
                    [
                        r["team"],
                        r["model"],
                        "answer" if r["service"] == "llm" else "training run",
                        r["outputs"],
                        r["failed_runs"],
                        money(r["cost_micro_per_output"]),
                    ]
                    for r in latest_units
                    if r["service"] in {"llm", "training"}
                ],
            ),
            table(
                "Answer cost components",
                ["Team", "Model", "Component", "Cost"],
                [
                    [r["team"], r["model"], k, money(v)]
                    for r in latest_units
                    for k, v in r["components_micro"].items()
                ],
            ),
            table(
                "Experiment ledger",
                ["Experiment", "Completed", "Failed", "Direct cost"],
                [
                    [
                        r["experiment_id"],
                        r["completed_runs"],
                        r["failed_runs"],
                        money(r["cost_micro"]),
                    ]
                    for r in m["experiments"]
                ],
            ),
        ],
        "The throughput conversion and model quality scores are simulator assumptions. A zero next-batch cost means the next batch fits the reserved capacity. A zero denominator is not reported as a free output.",
    )
    pages["anomalies"] = page(
        "Find the sweep before the invoice.",
        "Seasonal MAD and positive CUSUM are calibrated on development data with a false-alarm budget. Hourly and daily team, service and SKU series are scored on held-out months.",
        [
            table(
                "Held-out detection",
                ["Event recall", "Alert precision", "Point recall", "Burn before detection"],
                [
                    [
                        percent(d["event_recall"]),
                        percent(d["point_precision"]),
                        percent(d["point_recall"]),
                        money(d["burned_before_detection_micro"]),
                    ]
                ],
            ),
            table(
                "Incident record",
                ["Incident", "Team", "Start", "First alert", "Delay hours", "Avoidable cost"],
                [
                    [
                        r["id"],
                        r["team"],
                        r["start"],
                        r["first_alert"] or "Missed",
                        r["delay_hours"],
                        money(r["counterfactual_avoidable_micro"]),
                    ]
                    for r in d["events"]
                ],
            ),
            table(
                "Calibration and boundaries",
                [
                    "Grain",
                    "Team",
                    "Service",
                    "SKU",
                    "Method",
                    "Threshold",
                    "Dev false alarms",
                    "Interior",
                ],
                [
                    [
                        r["grain"],
                        r["team"],
                        r["service"],
                        r["sku"],
                        r.get("method", "Unscored: no development history"),
                        r.get("threshold"),
                        percent(r.get("false_alarm_rate")),
                        str(r.get("interior", False)),
                    ]
                    for r in d["series"]
                ],
            ),
        ],
        "Zero-hour detections are boundary results from timestamped synthetic incidents, not evidence of zero production latency. Event recall and point precision answer different questions. Post-development SKUs with no calibration history are unscored.",
    )
    pages["forecast"] = page(
        "A forecast earns its interval.",
        "Seasonal naive, trend-seasonal and gradient boosting compete only on development history. Daily and monthly rolling-origin predictions are evaluated separately; intervals use earlier residuals.",
        [
            table(
                "Daily held-out scorecard",
                ["Grain", "Series", "Selected", "MAE USD/day", "90% interval coverage"],
                [
                    [
                        r["grain"],
                        r["key"],
                        r["method"],
                        money(r["mae"], False),
                        percent(r["coverage"]),
                    ]
                    for r in m["forecasts"]
                ],
            ),
            table(
                "Monthly forecasts",
                ["Series", "Period", "Point", "Lower", "Upper", "Actual", "Covered"],
                [
                    [
                        r["grain"] + "/" + r["key"],
                        v["period"],
                        money(v["point"], False),
                        money(v["lower"], False),
                        money(v["upper"], False),
                        money(v["actual"], False),
                        str(v["covered"]),
                    ]
                    for r in m["forecasts"]
                    for v in r["monthly"]
                ],
            ),
            table(
                "Budget burn · latest observation",
                [
                    "Series",
                    "Date",
                    "Budget",
                    "Spent",
                    "Month-end projection",
                    "Exhaustion day",
                    "Severity",
                ],
                [
                    [
                        r["grain"] + "/" + r["key"],
                        r["rows"][-1]["date"],
                        money(r["budget"], False),
                        money(r["rows"][-1]["spent"], False),
                        money(r["rows"][-1]["projected_month_end"], False),
                        r["rows"][-1]["projected_exhaustion_day"],
                        r["rows"][-1]["severity"],
                    ]
                    for r in m["budgets"]
                ],
            ),
        ],
        "Team forecasts use direct spend, while statements include shared allocation. Serial dependence can invalidate nominal conformal coverage. Inadequate monthly calibration produces an unavailable interval. Live future forecasts are kept separate from these synthetic backtests.",
    )
    pages["recommendations"] = page(
        "Free capacity is not cash saved.",
        "Each action is estimated from observed telemetry, then independently rerun against the whole simulated platform. Shared-capacity effects can reduce savings or increase cost.",
        [
            table(
                "Whole-platform counterfactuals",
                ["Action", "Estimated annual", "True annual change", "Estimation error"],
                [
                    [
                        r["action"],
                        money(r["estimated_annual_micro"]),
                        money(r["true_platform_annual_micro"]),
                        money(r["error_micro"]),
                    ]
                    for r in actions["actions"]
                ],
            ),
            table(
                "Resource estimates and uncertainty",
                [
                    "Resource",
                    "Action",
                    "Monthly estimate",
                    "90% lower",
                    "90% upper",
                    "Resource truth covered",
                ],
                [
                    [
                        r["resource"],
                        r["action"],
                        money(r["estimated_monthly_micro"]),
                        money(r["monthly_lower_micro"]),
                        money(r["monthly_upper_micro"]),
                        str(r["monthly_interval_covers_resource_saving"]),
                    ]
                    for r in actions["rows"]
                ],
            ),
            table(
                "Combined rerun",
                ["Joint saving", "Share of baseline", "Share of registered avoidable reference"],
                [
                    [
                        money(actions["joint_recovered_micro"]),
                        percent(actions["recovery_share_of_baseline"]),
                        percent(actions["share_of_total_waste_recovered"]),
                    ]
                ],
            ),
        ],
        actions["overlap_note"]
        + " The avoidable reference combines registered actions and incident removal; it is not a proof of the global optimum. Resampled estimate intervals are not guaranteed cash-saving intervals. Model switching requires the registered quality floor.",
    )
    pages["commitments"] = page(
        "Buy the floor, measure the regret.",
        "Capacity is selected on development demand using actual locked public offer rates. Held-out regret is relative to the best registered capacity with hindsight.",
        [
            table(
                "Chosen capacity",
                ["Pool", "Offer", "Units", "Interior", "Unused hours", "Overflow hours"],
                [
                    [
                        r["pool"],
                        r["offer_id"],
                        r["selected_capacity"],
                        str(r["interior"]),
                        round(r["unused_commitment_hours"], 2),
                        round(r["overflow_hours"], 2),
                    ]
                    for r in m["commitments"]
                ],
            ),
            table(
                "Commitment sensitivity",
                ["Pool", "Multiplier", "Capacity", "Held-out USD/hour", "Regret USD/hour"],
                [
                    [
                        r["pool"],
                        v["multiplier"],
                        round(v["capacity"], 2),
                        f"${v['heldout_cost_per_hour']:.5f}",
                        f"${v['regret_per_hour']:.5f}",
                    ]
                    for r in m["commitments"]
                    for v in r["variants"]
                ],
            ),
            table(
                "Development objective",
                ["Pool", "Candidate capacity", "USD/hour"],
                [
                    [r["pool"], v["capacity"], f"${v['development_cost_per_hour']:.5f}"]
                    for r in m["commitments"]
                    for v in r["development_curve"]
                ],
            ),
        ],
        "Fractional perturbations are analytical sensitivity points, not necessarily purchasable units. No commitment was purchased. Future demand and provider offer availability can change.",
    )
    pages["portfolio"] = page(
        "The free tier still used compute.",
        "Public Actions jobs include every attempt in the recorded window. Committed ledgers preserve measured output and token counts. Unknown prices remain unknown.",
        [
            table(
                "CI shadow subtotal",
                ["Repository", "Runs", "Jobs", "Unpriced jobs", "Known shadow subtotal"],
                [
                    [
                        r["repository"],
                        r["runs"],
                        r["jobs"],
                        r["unpriced_jobs"],
                        money(r["shadow_cost_micro"]),
                    ]
                    for r in portfolio["rows"]
                ],
                "Job minutes round up individually. Public Linux runner usage is priced at the private paid equivalent; this is not an actual payment.",
            ),
            table(
                "Committed source coverage",
                ["Repository", "Source status", "Source files"],
                [[r["repository"], r["status"], len(r["paths"])] for r in ledger["inventory"]]
                + [[r["repository"], r["status"], 0] for r in ledger["absent"]],
            ),
            table(
                "Trajectory model panel",
                [
                    "Model",
                    "Runs",
                    "Input tokens",
                    "Output tokens",
                    "Completed outputs",
                    "Solved",
                    "Paid equivalent",
                ],
                [
                    [
                        name,
                        v["rows"],
                        v["tokens_in"],
                        v["tokens_out"],
                        v["outputs"],
                        v["solved"],
                        "Not priced: exact provider SKU unavailable",
                    ]
                    for name, v in ledger["model_totals"].items()
                ],
            ),
            table(
                "Usage window",
                ["Start inclusive", "End exclusive", "Committed records", "CI subtotal"],
                [
                    [
                        ledger["request"]["start"],
                        ledger["request"]["end_exclusive"],
                        ledger["row_count"],
                        money(portfolio.get("priced_subtotal_micro")),
                    ]
                ],
            ),
        ],
        "These are measured public records at shadow prices. Runner-contained work is not charged twice. Missing GPU ledgers, unknown NIM token rates and unmatched Databricks SKUs prevent a complete total. Undated answer evaluations are excluded from the window. No per-refresh or per-answer total is invented from unrelated CI jobs.",
    )
    pages["estimate"] = page(
        "Price the capacity you need.",
        "Compare hosting classes and token components using caller-supplied throughput. A live estimate is saved before its response; offline calculations are visibly labeled.",
        [],
        "A size class filters plausible options; it is not a memory-fit, latency or quality benchmark. Storage and network are excluded from this workload estimate.",
    )
    pages["data"] = page(
        "Follow the number back.",
        m["generation"]["price_basis"],
        [
            table(
                "Independent reconciliation",
                [
                    "Grain",
                    "Groups",
                    "Cost difference µUSD",
                    "Billed difference µUSD",
                    "Count difference",
                ],
                [
                    [
                        r["grain"],
                        r["groups"],
                        r["cost_difference_micro"],
                        r.get("billed_difference_micro"),
                        r["count_difference"],
                    ]
                    for r in m["reconciliation"]["checks"]
                ],
            ),
            table(
                "Locked price book",
                ["ID", "Provider", "SKU", "Region", "Term", "Unit", "USD", "Read on"],
                [
                    [
                        r[k]
                        for k in [
                            "id",
                            "provider",
                            "sku",
                            "region",
                            "term",
                            "unit",
                            "usd",
                            "retrieved_date",
                        ]
                    ]
                    for r in prices
                ],
            ),
            table(
                "Evidence fingerprints",
                ["Object", "SHA-256"],
                [
                    ["Observed charges", m["generation"]["observed_sha256"]],
                    ["Price book", m["generation"]["price_digest"]],
                    ["Registered protocol", m["registration"]["plan_digest"]],
                    ["Public ledger sources", ledger["source_digest"]],
                ],
            ),
        ],
        "FOCUS uses typed contracts and supplemental normative checks. The official validator's latest rule set contains a dependency cycle, and older rules contain documented contradictions. The raw official report is retained; full official certification is not claimed.",
    )
    pages["report"] = page(
        "Cost ownership is a set of choices.",
        "Read the statement, inspect what a policy moves, then test whether an intervention changes the total bill. The registered hypotheses below do not establish superiority.",
        [
            table(
                "Registered comparisons",
                [
                    "Hypothesis",
                    "Mean paired difference USD",
                    "95% cluster interval",
                    "Exact p",
                    "BH q",
                    "Significant",
                ],
                [
                    [
                        name,
                        f"${v['mean_difference_usd']:.4f}",
                        " to ".join(f"${x:.4f}" for x in v["cluster_bootstrap_95"]),
                        v["p_value"],
                        v["q_value"],
                        str(v["significant"]),
                    ]
                    for name, v in m["hypotheses"].items()
                ],
                "Negative favors the registered method. Teams are the resampling clusters. The correction family contains the registered allocation and forecast comparisons.",
            ),
            table(
                "Study dimensions",
                ["Charges", "Hours", "Effective cost", "Quarantined producer defects"],
                [
                    [
                        m["generation"]["rows"],
                        m["generation"]["hours"],
                        money(m["generation"]["total_micro"]),
                        m["reconciliation"]["quarantined"],
                    ]
                ],
            ),
        ],
        "This independent replication was registered after earlier version results were already known. The added long-term contract is a documented completeness correction. Simulated effects are not production savings. Created for Ajay Mekala with AI assistance.",
    )
    pages["playbook"] = page(
        "Use the bill to make a decision.",
        "A practical review path for an engineering lead, finance partner or interviewer.",
        [
            table(
                "Review sequence",
                ["Decision", "Evidence", "Action"],
                [
                    [
                        "Does the bill reconcile?",
                        "Source records and four-grain count/cost reconciliation",
                        "Stop if count or currency differs",
                    ],
                    [
                        "Who owns idle?",
                        "Allocation policies and idle-before-allocation table",
                        "Agree the policy before chargeback",
                    ],
                    [
                        "Can this reduce the bill?",
                        "Whole-platform counterfactual and capacity externality",
                        "Check whether a node can actually be removed",
                    ],
                    [
                        "Can we commit?",
                        "Development optimum and held-out regret",
                        "Keep uncertain demand on demand",
                    ],
                    [
                        "Is the API awake?",
                        "Two browser GET health attempts",
                        "Use visibly local calculation when unavailable",
                    ],
                    [
                        "Was it saved?",
                        "Returned identifier and independent readback",
                        "Never assume a timed-out POST failed",
                    ],
                ],
            )
        ],
        "Review the limitations beside each method. A recommendation is an experiment to validate, not authorization to change an unrelated production system.",
    )
    guide_paths = [
        "AGENTS.md",
        ".claude/skills/add-a-price-source/SKILL.md",
        ".claude/skills/add-a-cost-rule/SKILL.md",
        ".claude/skills/explain-a-bill/SKILL.md",
    ]
    guides = [
        {"path": p, "content": (root / p).read_text()} for p in guide_paths if (root / p).exists()
    ]
    payload = {
        "statement": STATEMENT,
        "latest_month": latest,
        "source_digest": digest(m),
        "pages": pages,
        "guides": guides,
        "charts": {
            "incidents": d["events"],
            "units": [
                r for r in m["units"] if r["month"] == latest and r["service"] == "inference"
            ],
            "commitments": m["commitments"],
            "holdout_start": "2025-09-01T00:00:00Z",
            "holdout_end": "2026-01-01T00:00:00Z",
            "forecast": {"key": m["forecasts"][0]["key"], "rows": m["forecasts"][0]["rows"]},
        },
        "allocations": m["allocation"],
        "monthly": [
            {"month": month, "effective_micro": cost}
            for month, cost in m["generation"]["monthly_micro"].items()
        ],
        "prices": prices,
        "sources": sorted({r["source_url"] for r in prices}),
        "metrics": {
            "effective": money(m["generation"]["monthly_micro"][latest]),
            "idle": money(sum(r["idle_micro"] for r in m["idle"] if r["month"] == latest)),
            "portfolio": money(portfolio.get("priced_subtotal_micro")),
        },
    }
    _write_or_check(root / "web/expanded.json", canonical(payload), check)
    for name, p in pages.items():
        content = (
            "# "
            + p["title"]
            + "\n\n"
            + STATEMENT
            + "\n\n"
            + p["intro"]
            + "".join(markdown(s) for s in p["sections"])
            + "\n## Limits and pushback\n\n"
            + p["limit"]
            + "\n"
        )
        _write_or_check(
            root / ("report/briefing.md" if name == "report" else f"docs/methods/{name}.md"),
            content.encode(),
            check,
        )
    sweep = next(r for r in d["events"] if r["id"] == "weekend-sweep")
    budget = next(r for r in m["budgets"] if r["grain"] == "team" and r["key"] == sweep["team"])
    candidates = [
        r
        for r in budget["rows"]
        if r["date"] >= sweep["start"][:10]
        and r["date"] <= sweep["end"][:10]
        and r["severity"] == "critical"
    ]
    budget_observed = (
        (datetime.fromisoformat(candidates[0]["date"]) + timedelta(days=1)).isoformat() + "+00:00"
        if candidates
        else None
    )
    budget_delay = (
        (
            datetime.fromisoformat(budget_observed) - datetime.fromisoformat(sweep["start"])
        ).total_seconds()
        / 3600
        if budget_observed
        else None
    )
    incident_report = (
        "# The weekend sweep\n\n"
        + STATEMENT
        + "\n\n## Impact\n\nA planted retry amplification increased research training demand. The incident-removal counterfactual isolates its platform-level effect; it is not summed into overlapping action savings.\n"
    )
    incident_report += markdown(
        table(
            "Observed timeline and counterfactual",
            [
                "Start",
                "End",
                "First detector alert",
                "Delay hours",
                "Burn before detection",
                "Avoidable cost",
                "First daily critical budget observation",
                "Budget observation delay hours",
            ],
            [
                [
                    sweep["start"],
                    sweep["end"],
                    sweep["first_alert"],
                    sweep["delay_hours"],
                    money(sweep["burned_before_detection_micro"]),
                    money(sweep["counterfactual_avoidable_micro"]),
                    budget_observed,
                    budget_delay,
                ]
            ],
        )
    )
    incident_report += "\n## Cause and detection\n\nThe simulator deliberately increased retrying training work. The method did not read the planted schedule: it consumed the observed cost series and development-calibrated seasonal residuals. Evaluation alone joined alerts to the incident window. The zero-delay result reflects the observation timestamp and synthetic step change; it is not a production response-time guarantee. Daily budget values become observable at the end of the day, and a critical budget flag does not identify a retry cause.\n\n## Corrective experiment\n\nBound retries, checkpoint interrupted work and inspect whole-node release before treating a cheaper rate as savings. The existing counterfactual evaluator measures independent and joint actions. A production remediation was not performed. The optional budget refusal service remains outside this release.\n\n## What would change the conclusion\n\nDelayed billing arrival, unknown incident boundaries, smaller gradual changes and missing provider metadata can worsen detection. The low alert precision alongside high event recall is retained rather than hidden by a favorable incident-only score.\n"
    _write_or_check(root / "docs/incidents/weekend-sweep.md", incident_report.encode(), check)
    for row in m["allocation"]:
        sections = [
            table(
                "Allocation policy",
                ["Method", "Statement"],
                [[k, money(v)] for k, v in row["methods"].items()],
            )
        ]
        team_units = [
            r for r in m["units"] if r["month"] == row["month"] and r["team"] == row["team"]
        ]
        if team_units:
            sections.append(
                table(
                    "Workloads",
                    ["Model", "Service", "Outputs", "Fully loaded", "Cost / output"],
                    [
                        [
                            r["model"],
                            r["service"],
                            r["outputs"],
                            money(r["fully_loaded_micro"]),
                            money(r["cost_micro_per_output"]),
                        ]
                        for r in team_units
                    ],
                )
            )
        forecasts = [
            v
            for f in m["forecasts"]
            if f["grain"] == "team" and f["key"] == row["team"]
            for v in f["monthly"]
            if v["period"] == row["month"]
        ]
        if forecasts:
            sections.append(
                table(
                    "Direct-spend forecast",
                    ["Period", "Point", "Lower", "Upper", "Actual"],
                    [
                        [
                            v["period"],
                            money(v["point"], False),
                            money(v["lower"], False),
                            money(v["upper"], False),
                            money(v["actual"], False),
                        ]
                        for v in forecasts
                    ],
                )
            )
        incidents = [
            r for r in d["events"] if r["team"] == row["team"] and r["start"][:7] == row["month"]
        ]
        sections.append(
            table(
                "Incidents starting this month",
                ["Incident", "First alert", "Avoidable counterfactual"],
                [
                    [r["id"], r["first_alert"], money(r["counterfactual_avoidable_micro"])]
                    for r in incidents
                ]
                or [
                    [
                        "No held-out incident started in this team-month",
                        "Not applicable",
                        "Not applicable",
                    ]
                ],
            )
        )
        content = (
            f"# {row['team']} · {row['month']}\n\n{STATEMENT}\n\nMethod of record: usage. Direct cost {money(row['direct_micro'])}; idle and shared allocation {money(row['methods']['usage'] - row['direct_micro'])}.\n"
            + "".join(markdown(s) for s in sections)
            + "\nReview docs/methods/recommendations.md before changing capacity. Forecasts use direct spend and are not directly comparable to fully loaded statements. Source: results/expanded/manifest.json; allocation conserves integer microdollars.\n"
        )
        _write_or_check(
            root / f"report/statements/{row['month']}-{row['team']}.md", content.encode(), check
        )
    requirements = read_json(root / "config/completion.json")
    results = (
        "# Results\n\n"
        + STATEMENT
        + "\n\nThe expanded study is implemented. Release status is determined by the evidence below; an unavailable source or skipped check is never a pass.\n"
    )
    results += markdown(
        table(
            "Required checklist",
            ["Requirement", "Status", "Evidence or limit"],
            [[r["requirement"], r["status"], r["evidence"]] for r in requirements],
        )
    )
    results += "\n" + "\n".join("## " + p["title"] + "\n\n" + p["limit"] for p in pages.values())
    results += "\n" + markdown(pages["report"]["sections"][0])
    _write_or_check(root / "RESULTS.md", results.encode(), check)
    readme = (
        "# MLSpend\n\n[Live dashboard](https://mekala27-45.github.io/mlspend/) · [API health](https://mlspend.vercel.app/health) · [Verification and limits](RESULTS.md)\n\n"
        + STATEMENT
        + "\n\nA cost observability project with a simulated platform book and a measured public-portfolio book. It compares ownership policies, unit economics, forecasts, anomaly detection and whole-platform counterfactuals.\n"
    )
    readme += markdown(pages["report"]["sections"][1])
    readme += "\n## Run\n\n```sh\nuv sync --group dev\nuv run python -m scripts.build\nuv run python -m scripts.build_expanded\nuv run pytest --cov=packages\nuv run python -m scripts.check\nuv run python -m scripts.serve_local\n```\n\nFor the Next.js site, run `npm ci` and `npm run dev` inside `web`. Hosted persistence needs the scoped DATABASE_URL and MLSPEND_SALT. Run Alembic with a separate migration credential before serving. No credentials belong in source control.\n"
    readme += markdown(
        table(
            "Skills and evidence",
            ["Skill", "Inspectable evidence"],
            [
                [
                    "Deterministic simulation and counterfactuals",
                    "packages/simulator; packages/evaluation; evaluation/v2",
                ],
                [
                    "FOCUS and exact reconciliation",
                    "packages/focus; packages/warehouse; warehouse-expanded",
                ],
                ["Allocation and Shapley capacity", "packages/allocation; packages/expansion"],
                ["Unit economics and commitments", "packages/optimize; exports/expanded"],
                ["Forecasting and detection", "packages/forecast; packages/detect"],
                [
                    "Public-source measurement",
                    "scripts/fetch_committed_ledgers.py; results/committed-ledgers.json",
                ],
                ["API, migrations and persistence", "packages/api; migrations; Dockerfile.vercel"],
                [
                    "Reproducible reporting and browser UI",
                    "packages/render; web/app; .github/workflows",
                ],
            ],
        )
    )
    readme += (
        "\n## Interpretation\n\n"
        + pages["report"]["limit"]
        + "\n\n"
        + pages["portfolio"]["limit"]
        + "\n\nSee RESULTS.md for validation status, source gaps and release gates. The public price snapshot is a scenario input, not a historical invoice.\n\n## License\n\nApache-2.0 for project code. Public price and usage records retain their original provider terms; see DATA_SOURCES.md.\n"
    )
    pending = [
        r["requirement"]
        for r in requirements
        if "pending" in r["status"].lower() or "progress" in r["status"].lower()
    ]
    if pending:
        readme = readme.replace(
            "# MLSpend\n\n",
            "# MLSpend\n\nRelease remains incomplete: "
            + "; ".join(pending)
            + ". See RESULTS.md for the exact checks and limits.\n\n",
            1,
        )
    _write_or_check(root / "README.md", readme.encode(), check)


if __name__ == "__main__":
    render()
