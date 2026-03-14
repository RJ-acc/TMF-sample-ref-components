# Product Order Capture & Validation source

This source tree mirrors the packaging style of the TM Forum `ProductCatalog` example component, but implements a lighter Python-based reference for `TMFC002`.

## Microservices

- `productOrderCaptureValidationMicroservice/implementation`
  The core TMF622-style Product Order API.
- `orderValidationMicroservice/implementation`
  Internal validation endpoints used by the order API before state progression.
- `partyRoleMicroservice/implementation`
  Lightweight TMF669-style Party Role API for the security function.
- `openMetricsMicroservice`
  Prometheus-compatible metrics listener for order event notifications.
- `roleInitializationMicroservice/implementation`
  Job script that seeds the initial canvas role.
- `productOrderInitializationMicroservice/implementation`
  Job script that registers the metrics listener as a subscriber on the order API.
- `MCPServerMicroservice`
  Optional MCP wrapper over the TMF622 API.

## Local development

Install dependencies:

```bash
pip install -r source/ProductOrderCaptureValidation/requirements.txt
```

Run the validation service:

```bash
uvicorn orderValidationMicroservice.implementation.app:app --app-dir source/ProductOrderCaptureValidation --port 8081 --reload
```

Run the order API:

```bash
uvicorn productOrderCaptureValidationMicroservice.implementation.app:app --app-dir source/ProductOrderCaptureValidation --port 8080 --reload
```

Run the party role API:

```bash
uvicorn partyRoleMicroservice.implementation.app:app --app-dir source/ProductOrderCaptureValidation --port 8090 --reload
```

Run the metrics listener:

```bash
uvicorn openMetricsMicroservice.app:app --app-dir source/ProductOrderCaptureValidation --port 4000 --reload
```

## Scope

This is a reference baseline, not a full TMF622 certification target. The implementation focuses on:

- component structure
- Helm deployability
- order capture plus validation behavior
- event publication and metrics subscription
- optional AI-facing MCP access

