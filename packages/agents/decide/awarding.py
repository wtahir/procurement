from packages.core.models.order import ProcurementOrder
from packages.tools.pricing_tools import rank_quotes_by_total


def choose_lowest_bid(order: ProcurementOrder) -> ProcurementOrder:
    quotes = rank_quotes_by_total(order.bidding.quotes_received)
    if quotes:
        order.bidding.recommended_bid = quotes[0].model_dump()
    return order
