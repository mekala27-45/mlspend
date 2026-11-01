import argparse
import os
from datetime import UTC, datetime

from packages.api.storage import Store
from packages.core.io import ROOT, read_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("period")
    parser.add_argument("--actuals", required=True)
    arguments = parser.parse_args()
    store = Store(os.environ["DATABASE_URL"], os.environ["MLSPEND_SALT"])
    actuals = read_json(ROOT / arguments.actuals)
    print({"scored": store.close_period(arguments.period, actuals, datetime.now(UTC))})


if __name__ == "__main__":
    main()
