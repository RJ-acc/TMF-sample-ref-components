# TMFC027 Product Configurator

This folder contains a reference-style `TMFC027` component scaffold built around `TMF760 Product Configuration Management`.

It mirrors the same broad packaging model as the sample TM Forum reference components:

- a Helm chart under `charts/ProductConfigurator`
- a source tree under `source/ProductConfigurator`
- a TMF760-based core API for `queryProductConfiguration` and `checkProductConfiguration`
- an internal configuration engine microservice for validation and deterministic configuration shaping
- metrics, role bootstrap, and event-registration bootstrap jobs
- an optional MCP wrapper for AI-facing access

The implementation is intentionally a lightweight runnable baseline rather than a certification target. The goal is to provide a clear component shape, deployment model, and pragmatic starter services for configuration-query and configuration-check flows.

Key assumptions in this scaffold:

- `TMFC027` is modeled around `TMF760 Product Configuration Management`
- the public API exposes the spec-defined operations for `queryProductConfiguration`, `checkProductConfiguration`, event subscription, and listener examples
- `TMF760` does not define `patch` or `delete` on the main product-configuration resources, so those operations are intentionally not implemented
- the configuration engine uses a small in-repo starter catalog and deterministic rules for actions, terms, characteristics, and basic price shaping
- the security function is simplified to `TMF669 Party Role Management`
- the MCP wrapper is optional and disabled by default in the Helm values

Start with:

- `charts/ProductConfigurator/README.md`
- `source/ProductConfigurator/README.md`
