from packages.core.models.order import ProcurementOrder


def choose_lowest_bid(order: ProcurementOrder) -> ProcurementOrder:
    quotes = sorted(order.bidding.quotes_received, key=lambda quote: quote.total)
    if quotes:
        winner = quotes[0]
        order.bidding.recommended_bid = winner.model_dump()
    return order
