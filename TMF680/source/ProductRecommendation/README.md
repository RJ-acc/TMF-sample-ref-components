# Product Recommendation source

This source tree mirrors the packaging style of the TM Forum sample component, but implements a lighter Python-based reference for `TMFC050 Product Recommendation`.

## Microservices

- `productRecommendationMicroservice/implementation`
  The core TMF680-style Recommendation API exposing `queryProductRecommendation`.
- `recommendationEngineMicroservice/implementation`
  Internal validation and deterministic ranking service used by the API.
- `partyRoleMicroservice/implementation`
  Lightweight TMF669-style Party Role API for the security function.
- `openMetricsMicroservice`
  Prometheus-text metrics listener for recommendation events.
- `roleInitializationMicroservice/implementation`
  Job script that seeds the initial canvas role.
- `productRecommendationInitializationMicroservice/implementation`
  Job script that registers the metrics listener as a subscriber on the recommendation API.
- `MCPServerMicroservice`
  Optional MCP wrapper over the TMF680 API.

## Local development

Install dependencies:

```bash
pip install -r TMF680/source/ProductRecommendation/requirements.txt
```

Run the recommendation engine:

```bash
uvicorn recommendationEngineMicroservice.implementation.app:app --app-dir TMF680/source/ProductRecommendation --port 8081 --reload
```

Run the recommendation API:

```bash
uvicorn productRecommendationMicroservice.implementation.app:app --app-dir TMF680/source/ProductRecommendation --port 8080 --reload
```

Run the party role API:

```bash
uvicorn partyRoleMicroservice.implementation.app:app --app-dir TMF680/source/ProductRecommendation --port 8090 --reload
```

Run the metrics listener:

```bash
uvicorn openMetricsMicroservice.app:app --app-dir TMF680/source/ProductRecommendation --port 4000 --reload
```

Run the test suite:

```bash
python3 -m unittest discover -s TMF680/source/ProductRecommendation/tests -v
```

## Scope

This is a reference baseline, not a full TMF680 certification target. The implementation focuses on:

- component structure
- Helm deployability
- spec-aligned `list`, `create`, and `retrieve` behavior for `queryProductRecommendation`
- event publication and metrics subscription
- a small but understandable recommendation-generation flow
- optional AI-facing MCP access
