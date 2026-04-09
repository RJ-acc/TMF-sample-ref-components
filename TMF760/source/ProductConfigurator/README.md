# Product Configurator source

This source tree mirrors the packaging style of the TM Forum sample component, but implements a lighter Python-based reference for `TMFC027 Product Configurator`.

## Microservices

- `productConfigurationMicroservice/implementation`
  The core TMF760-style Product Configuration API exposing `queryProductConfiguration` and `checkProductConfiguration`.
- `configurationEngineMicroservice/implementation`
  Internal validation and deterministic configuration service used by the API.
- `partyRoleMicroservice/implementation`
  Lightweight TMF669-style Party Role API for the security function.
- `openMetricsMicroservice`
  Prometheus-text metrics listener for product-configuration events.
- `roleInitializationMicroservice/implementation`
  Job script that seeds the initial canvas role.
- `productConfigurationInitializationMicroservice/implementation`
  Job script that registers the metrics listener as a subscriber on the product-configuration API.
- `MCPServerMicroservice`
  Optional MCP wrapper over the TMF760 API.

## Local development

Install dependencies:

```bash
pip install -r TMF760/source/ProductConfigurator/requirements.txt
```

Run the configuration engine:

```bash
uvicorn configurationEngineMicroservice.implementation.app:app --app-dir TMF760/source/ProductConfigurator --port 8081 --reload
```

Run the product-configuration API:

```bash
uvicorn productConfigurationMicroservice.implementation.app:app --app-dir TMF760/source/ProductConfigurator --port 8080 --reload
```

Run the party role API:

```bash
uvicorn partyRoleMicroservice.implementation.app:app --app-dir TMF760/source/ProductConfigurator --port 8090 --reload
```

Run the metrics listener:

```bash
uvicorn openMetricsMicroservice.app:app --app-dir TMF760/source/ProductConfigurator --port 4000 --reload
```

Run the test suite:

```bash
python3 -m unittest discover -s TMF760/source/ProductConfigurator/tests -v
```

## Scope

This is a reference baseline, not a full TMF760 certification target. The implementation focuses on:

- component structure
- Helm deployability
- spec-aligned `list`, `create`, and `retrieve` behavior for `queryProductConfiguration` and `checkProductConfiguration`
- event publication and metrics subscription
- a small but understandable configuration-generation and configuration-check flow
- optional AI-facing MCP access
