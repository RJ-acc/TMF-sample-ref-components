# TMFC002 Product Order Capture & Validation

This folder contains a reference-style `TMFC002` component scaffold built to mirror the overall approach used by the TM Forum `ProductCatalog` example component:

- a Helm chart under `charts/ProductOrderCaptureValidation`
- a source tree under `source/ProductOrderCaptureValidation`
- a TMF622-based core API for product order capture
- an internal validation microservice
- metrics, role bootstrap, and order-event bootstrap jobs
- an optional MCP wrapper for AI-facing access

The implementation is intentionally a lightweight reference baseline rather than a full TMF622 conformance implementation. The goal is to give you a component structure, deployment model, and runnable starter services that follow the same packaging pattern as the upstream example.

Key assumptions in this scaffold:

- TMFC002 is modelled around `TMF622 Product Ordering Management`
- the validation capability is implemented as an internal microservice used by the order API
- the security function is simplified to `TMF669 Party Role Management`
- the MCP wrapper is optional in the Helm chart, matching the optional style used by the ProductCatalog reference chart

Start with:

- `charts/ProductOrderCaptureValidation/README.md`
- `source/ProductOrderCaptureValidation/README.md`

