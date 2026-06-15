from packages.core.models.order import QuoteRecord


def rank_quotes_by_total(quotes: list[QuoteRecord]) -> list[QuoteRecord]:
    return sorted(quotes, key=lambda quote: quote.total)


def detect_price_outlier(quotes: list[QuoteRecord], threshold_ratio: float = 0.25) -> bool:
    if len(quotes) < 2:
        return False
    values = [quote.total for quote in quotes]
    lowest = min(values)
    highest = max(values)
    return lowest > 0 and (highest - lowest) / lowest >= threshold_ratio
