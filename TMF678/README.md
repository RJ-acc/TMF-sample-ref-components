# TMFC030 Bill Generation Management

This folder contains a reference-style `TMFC030` component scaffold built around `TMF678 Customer Bill Management`.

It mirrors the same broad packaging model used for the other components in this repo:

- a Helm chart under `charts/BillGenerationManagement`
- a source tree under `source/BillGenerationManagement`
- a TMF678-based core API for `appliedCustomerBillingRate`, `billCycle`, `customerBill`, and `customerBillOnDemand`
- an internal bill-generation engine for deterministic on-demand bill creation
- metrics, role bootstrap, and event-registration bootstrap jobs
- an optional MCP wrapper for AI-facing access

Key assumptions in this scaffold:

- `TMFC030` is modeled around `TMF678 Customer Bill Management`
- the public API exposes the spec-defined operations for read-only billing catalogs, customer-bill retrieval and patch, customer-bill-on-demand creation, event subscription, and listener examples
- only the methods defined by TMF678 are implemented; unsupported create/update/delete combinations are intentionally left to return `405`
- the bill-generation engine uses a small in-repo starter billing dataset and deterministic rules to create bills on demand
- the security function is simplified to `TMF669 Party Role Management`
- the MCP wrapper is optional and disabled by default in the Helm values

Start with:

- `charts/BillGenerationManagement/README.md`
- `source/BillGenerationManagement/README.md`
