from packages.core.models.order import QuoteRecord
from packages.tools.pricing_tools import detect_price_outlier, rank_quotes_by_total


def test_rank_quotes_by_total_returns_lowest_first() -> None:
    quotes = [
        QuoteRecord(
            supplier_id="s2",
            unit_price=12,
            total=120,
            lead_time_days=3,
            terms="cash",
            reliability_score=0.9,
            raw_ref="b",
        ),
        QuoteRecord(
            supplier_id="s1",
            unit_price=10,
            total=100,
            lead_time_days=3,
            terms="cash",
            reliability_score=0.9,
            raw_ref="a",
        ),
    ]

    ranked = rank_quotes_by_total(quotes)

    assert ranked[0].supplier_id == "s1"


def test_detect_price_outlier_flags_large_spread() -> None:
    quotes = [
        QuoteRecord(
            supplier_id="s1",
            unit_price=10,
            total=100,
            lead_time_days=3,
            terms="cash",
            reliability_score=0.9,
            raw_ref="a",
        ),
        QuoteRecord(
            supplier_id="s2",
            unit_price=15,
            total=160,
            lead_time_days=3,
            terms="cash",
            reliability_score=0.9,
            raw_ref="b",
        ),
    ]

    assert detect_price_outlier(quotes) is True
