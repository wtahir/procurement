from __future__ import annotations

from httpx import AsyncClient

from packages.adapters.base import RFQHandle, SupplierAdapter
from packages.core.models.quote import QuoteError, QuotePending, StandardQuote
from packages.core.models.rfq import StandardRFQ
from packages.core.models.supplier import SupplierDescriptor


class RestSupplierAdapter(SupplierAdapter):
    def __init__(self, descriptor: SupplierDescriptor, base_url: str) -> None:
        self.descriptor = descriptor
        self.supplier_id = descriptor.supplier_id
        self.base_url = base_url.rstrip("/")

    async def send_rfq(self, rfq: StandardRFQ) -> RFQHandle:
        async with AsyncClient() as client:
            response = await client.post(f"{self.base_url}/rfq", json=rfq.model_dump(mode="json"))
            response.raise_for_status()
            payload = response.json()
        return RFQHandle(self.supplier_id, str(payload["quote_id"]))

    async def get_quote(self, handle: RFQHandle) -> StandardQuote | QuotePending | QuoteError:
        return QuotePending(supplier_id=handle.supplier_id, handle_id=handle.handle_id)

    async def health_check(self) -> bool:
        async with AsyncClient() as client:
            response = await client.get(f"{self.base_url}/catalog")
        return response.is_success
