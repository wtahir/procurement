# Architecture

Procura uses an explicit staged workflow:

1. Intake
2. Source
3. Decide
4. Approve
5. Fulfill

The load-bearing contracts are the shared `ProcurementOrder` state model and the `SupplierAdapter` interface. Every downstream service is designed to extend one of those contracts instead of inventing a new shape.
