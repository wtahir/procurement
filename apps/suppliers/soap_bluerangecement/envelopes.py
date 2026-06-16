def quote_request_envelope(rfq_id: str) -> str:
    return f"<Envelope><Body><QuoteRequest id=\"{rfq_id}\" /></Body></Envelope>"
