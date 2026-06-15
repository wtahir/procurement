from apps.suppliers.common.catalog import BASE_CATALOG


def quote_price(material_code: str, region: str, quantity: float, markup: float = 1.0) -> float:
    region_prices = BASE_CATALOG.get(material_code, {})
    base_price = region_prices.get(region.lower(), 100.0)
    quantity_factor = 0.97 if quantity >= 500 else 1.0
    return round(base_price * quantity_factor * markup, 2)
