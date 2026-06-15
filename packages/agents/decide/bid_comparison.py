from packages.core.models.order import ProcurementOrder


def rank_bids(order: ProcurementOrder) -> ProcurementOrder:
    quotes = sorted(order.bidding.quotes_received, key=lambda quote: quote.total)
    order.bidding.comparison_matrix = {
        "quote_count": len(quotes),
        "lowest_total": quotes[0].total if quotes else None,
    }
    return order
