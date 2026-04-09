# TMFC050 Product Recommendation

This folder contains a reference-style `TMFC050` component scaffold built around `TMF680 Recommendation`.

It mirrors the same broad packaging model as the sample TMFC002 component:

- a Helm chart under `charts/ProductRecommendation`
- a source tree under `source/ProductRecommendation`
- a TMF680-based core API for `queryProductRecommendation`
- an internal recommendation engine microservice for validation and ranking
- metrics, role bootstrap, and event-registration bootstrap jobs
- an optional MCP wrapper for AI-facing access

The implementation is intentionally a lightweight runnable baseline rather than a certification target. The goal is to provide a clear component shape, deployment model, and pragmatic starter services for recommendation flows.

Key assumptions in this scaffold:

- `TMFC050` is modeled around `TMF680 Recommendation`
- the public API exposes the spec-defined operations: `list`, `create`, `retrieve`, and event subscription
- `TMF680` does not define `patch` or `delete` on `queryProductRecommendation`, so those operations are intentionally not implemented
- the recommendation engine uses a small in-repo starter catalog and deterministic ranking rules
- the security function is simplified to `TMF669 Party Role Management`
- the MCP wrapper is optional and disabled by default in the Helm values

Start with:

- `charts/ProductRecommendation/README.md`
- `source/ProductRecommendation/README.md`
