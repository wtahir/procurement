def three_way_match(po_qty: float, delivery_qty: float, invoice_qty: float) -> bool:
    return po_qty == delivery_qty == invoice_qty
