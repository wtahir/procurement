from packages.core.models.order import ProcurementOrder, RFQRecord
from packages.core.models.supplier import SupplierDescriptor


def queue_rfqs(order: ProcurementOrder, suppliers: list[SupplierDescriptor]) -> ProcurementOrder:
    order.bidding.rfqs_sent.extend(
        RFQRecord(supplier_id=supplier.supplier_id, channel=supplier.channel.value) for supplier in suppliers
    )
    return order
