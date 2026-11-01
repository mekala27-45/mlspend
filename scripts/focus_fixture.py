"""Small development-only files for the official validator integration check."""

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
        [contract_row("simulated-t4-contract", "azure-t4", book)],
        target / "ContractCommitment.parquet",
        "ContractCommitment",
    )


if __name__ == "__main__":
    main()
