from db.seeds.market_prices import MARKET_PRICE_SEEDS
from db.seeds.materials import MATERIAL_SEEDS
from db.seeds.projects import PROJECT_SEEDS
from db.seeds.suppliers import SUPPLIER_SEEDS


def main() -> None:
    print(
        {
            "suppliers": len(SUPPLIER_SEEDS),
            "projects": len(PROJECT_SEEDS),
            "materials": len(MATERIAL_SEEDS),
            "market_prices": len(MARKET_PRICE_SEEDS),
        }
    )


if __name__ == "__main__":
    main()
