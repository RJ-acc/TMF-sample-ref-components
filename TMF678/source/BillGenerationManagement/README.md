# Bill Generation Management source

This source tree mirrors the packaging style of the TM Forum sample component, but implements a lighter Python-based reference for `TMFC030 Bill Generation Management`.

## Microservices

- `billGenerationManagementMicroservice/implementation`
  The core TMF678-style Customer Bill Management API exposing read-only bill data, `customerBill` patch, and `customerBillOnDemand` creation.
- `billGenerationEngineMicroservice/implementation`
  Internal validation and deterministic bill-generation service used by the API.
- `partyRoleMicroservice/implementation`
  Lightweight TMF669-style Party Role API for the security function.
- `openMetricsMicroservice`
  Prometheus-text metrics listener for TMF678 customer-bill events.
- `roleInitializationMicroservice/implementation`
  Job script that seeds the initial canvas role.
- `billGenerationInitializationMicroservice/implementation`
  Job script that registers the metrics listener as a subscriber on the customer-bill API.
- `MCPServerMicroservice`
  Optional MCP wrapper over the TMF678 API.

## Local development

Install dependencies:

```bash
pip install -r TMF678/source/BillGenerationManagement/requirements.txt
```

Run the bill-generation engine:

```bash
uvicorn billGenerationEngineMicroservice.implementation.app:app --app-dir TMF678/source/BillGenerationManagement --port 8081 --reload
```

Run the customer-bill API:

```bash
uvicorn billGenerationManagementMicroservice.implementation.app:app --app-dir TMF678/source/BillGenerationManagement --port 8080 --reload
```

Run the party role API:

```bash
uvicorn partyRoleMicroservice.implementation.app:app --app-dir TMF678/source/BillGenerationManagement --port 8090 --reload
```

Run the metrics listener:

```bash
uvicorn openMetricsMicroservice.app:app --app-dir TMF678/source/BillGenerationManagement --port 4000 --reload
```

Run the test suite:

```bash
python3 -m unittest discover -s TMF678/source/BillGenerationManagement/tests -v
```

## Scope

This is a reference baseline, not a full TMF678 certification target. The implementation focuses on:

- component structure
- Helm deployability
- spec-aligned list/get behavior for `appliedCustomerBillingRate` and `billCycle`
- spec-aligned list/get/patch behavior for `customerBill`
- spec-aligned list/create/get behavior for `customerBillOnDemand`
- event publication and metrics subscription
- a small but understandable bill-generation flow
- optional AI-facing MCP access
