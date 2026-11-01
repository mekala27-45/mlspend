from datetime import UTC, datetime
from decimal import Decimal
from urllib.parse import urlencode

from packages.core.io import ROOT, digest, read_json, write_json
from packages.prices.client import SourceClient


def main() -> None:
    request = read_json(ROOT / "requests/prices.json")
    client = SourceClient(ROOT / "tmp/http-cache")
    output = []
    for sku in request["azure_skus"]:
        query = {
            "$filter": f"armSkuName eq '{sku}' and armRegionName eq '{request['region']}'",
            "api-version": "2023-01-01-preview",
        }
        url = "https://prices.azure.com/api/retail/prices?" + urlencode(query)
        while url:
            page = client.get(url)
            for row in page["Items"]:
                if (
                    "Windows" in row["productName"]
                    or row["currencyCode"] != "USD"
                    or row["type"] == "DevTestConsumption"
                ):
                    continue
                amount = Decimal(str(row["retailPrice"]))
                output.append(
                    {
                        "provider": "Azure",
                        "sku": sku,
                        "region": row["armRegionName"],
                        "unit": row["unitOfMeasure"],
                        "amount": str(amount),
                        "term": row.get("reservationTerm", row["type"]),
                        "effective_date": row["effectiveStartDate"],
                        "source_url": url,
                        "source_row_digest": digest(row),
                        "raw": row,
                    }
                )
            url = page.get("NextPageLink")
    if not output:
        raise ValueError("Price fetch returned no rows")
    write_json(
        ROOT / "results/fetched-prices.json",
        {
            "request_digest": digest(request),
            "retrieved_at": datetime.now(UTC).isoformat(),
            "rows": output,
            "visited": client.visited,
            "promotion_status": "review_required",
        },
    )


if __name__ == "__main__":
    main()
