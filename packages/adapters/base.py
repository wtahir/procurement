from __future__ import annotations

from abc import ABC, abstractmethod

from packages.core.models.quote import QuoteError, QuotePending, StandardQuote
from packages.core.models.rfq import StandardRFQ
from packages.core.models.supplier import SupplierDescriptor


class RFQHandle:
    def __init__(self, supplier_id: str, handle_id: str) -> None:
        self.supplier_id = supplier_id
        self.handle_id = handle_id


class SupplierAdapter(ABC):
    supplier_id: str
    descriptor: SupplierDescriptor

    @abstractmethod
    async def send_rfq(self, rfq: StandardRFQ) -> RFQHandle:
        raise NotImplementedError

    @abstractmethod
    async def get_quote(self, handle: RFQHandle) -> StandardQuote | QuotePending | QuoteError:
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        raise NotImplementedError
