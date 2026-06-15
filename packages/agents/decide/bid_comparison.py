from packages.core.models.order import ProcurementOrder
from packages.tools.pricing_tools import rank_quotes_by_total


def rank_bids(order: ProcurementOrder) -> ProcurementOrder:
    quotes = rank_quotes_by_total(order.bidding.quotes_received)
    order.bidding.comparison_matrix = {
        "quote_count": len(quotes),
        "lowest_total": quotes[0].total if quotes else None,
    }
    return order
