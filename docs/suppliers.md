# Suppliers

The supplier layer deliberately mixes multiple integration styles so the adapter problem is real:

- REST/JSON
- SOAP/XML
- GraphQL
- Batch file drop
- Webhook/event-driven
- Fixed-width legacy

The pipeline never consumes supplier-native formats directly. It consumes canonical RFQ and quote models.
