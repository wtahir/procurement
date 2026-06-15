from packages.core.models.order import ProcurementOrder


def three_way_match(order: ProcurementOrder) -> ProcurementOrder:
    invoice = order.fulfilment.invoice
    if invoice.po_qty == invoice.delivery_qty == invoice.invoice_qty:
        invoice.match_result = "matched"
    else:
        invoice.match_result = "mismatch"
    return order
