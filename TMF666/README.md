# TMFC024 Billing Account Management

This folder contains a reference-style `TMFC024` component scaffold built around `TMF666 Account Management v5.0.0`.

The structure mirrors the pattern used for the other components in this repo:
- a Helm chart under `charts/BillingAccountManagement`
- a source tree under `source/BillingAccountManagement`
- a TMF666-based core API for `billFormat`, `billPresentationMedia`, `billingAccount`, `billingCycleSpecification`, `financialAccount`, `partyAccount`, and `settlementAccount`
- a metrics listener, role bootstrap job, Party Role API, and optional MCP wrapper

Notes:
- `TMFC024` is modeled around `TMF666 Account Management`
- all official TMF666 paths in the current `v5.0.0` OAS are implemented
- unsupported method combinations are intentionally left to return `405`

Start with:
- `charts/BillingAccountManagement/README.md`
- `source/BillingAccountManagement/README.md`
