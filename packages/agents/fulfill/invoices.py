from packages.core.models.order import ProcurementOrder
from packages.tools.matching_tools import three_way_match as quantities_match


def three_way_match(order: ProcurementOrder) -> ProcurementOrder:
    invoice = order.fulfilment.invoice
    quantities = (invoice.po_qty, invoice.delivery_qty, invoice.invoice_qty)
    matched = all(qty is not None for qty in quantities) and quantities_match(*quantities)
    invoice.match_result = "matched" if matched else "mismatch"
    return order
