"""Small development-only files for the official validator integration check."""

import duckdb

from packages.core.io import ROOT
from packages.focus.export import contract_row, cost_row, parquet
from packages.prices.book import PriceBook
from packages.simulator.expanded import simulate


def main() -> None:
    book = PriceBook(ROOT / "data/prices/expanded")
    target = ROOT / "tmp/focus-fixture"
    parquet(
        (cost_row(row, book) for row in simulate(book, hours=2)),
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
