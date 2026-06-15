from packages.core.models.order import OrderIdentity, ProcurementOrder, RequestPayload


def main() -> None:
    order = ProcurementOrder(
        identity=OrderIdentity(tenant_id="demo"),
        request=RequestPayload(raw_input="Need 500 tons of rebar in Riyadh"),
    )
    print(order.model_dump(mode="json"))


if __name__ == "__main__":
    main()
