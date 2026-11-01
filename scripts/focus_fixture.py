"""Small development-only files for the official validator integration check."""

import duckdb

from packages.core.io import ROOT
from packages.focus.export import contract_row, cost_row, parquet
from packages.prices.book import PriceBook
from packages.simulator.expanded import simulate


def main() -> None:
    book = PriceBook(ROOT / "data/prices/expanded")
    target = ROOT / "tmp/focus-fixture"
    observed = list(simulate(book, hours=2))
    # Exercise allocation objects in the fast official integration, not only
    # in the full-year export. Two halves conserve this development charge.
    origin = next(row for row in observed if row["team"] == "shared")
    allocated = [
        {
            **origin,
            "id": origin["id"] + "-fixture-" + team,
            "origin_id": origin["id"],
            "team": team,
            "cost_micro": origin["cost_micro"] // 2 + remainder,
            "pricing_quantity": origin["pricing_quantity"] / 2,
            "allocated_ratio": 0.5,
        }
        for team, remainder in (("ads", 0), ("research", origin["cost_micro"] % 2))
    ]
    parquet(
        (cost_row(row, book) for row in [*observed, *allocated]),
        target / "CostAndUsage.parquet",
        "CostAndUsage",
    )
    parquet(
        [
            contract_row("simulated-t4-contract", "azure-t4", book),
            contract_row("simulated-a100-contract-3y", "azure-a100", book, years=3),
        ],
        target / "ContractCommitment.parquet",
        "ContractCommitment",
    )
    # FOCUS 1.3 used ProviderName/PublisherName; preserve a separate compatibility view.
    with duckdb.connect() as connection:
        connection.sql(
            f"SELECT *, ServiceProviderName AS ProviderName, HostProviderName AS PublisherName FROM read_parquet('{target.as_posix()}/CostAndUsage.parquet')"
        ).write_parquet(str(target / "CostAndUsage-1.3.parquet"))


if __name__ == "__main__":
    main()
