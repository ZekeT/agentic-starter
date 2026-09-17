# Design

Use the existing database outbox with at most three retries. Retain the serializer
delivered by the first slice. Kafka rejected for operational cost.

Delivery must preserve tenant isolation.
