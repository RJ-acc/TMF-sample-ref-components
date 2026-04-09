from __future__ import annotations

from typing import Any

from fastapi import FastAPI

from common.recommendations import STARTER_CATALOG, generate_recommendations
from common.validation import RECOMMENDATION_TYPES, STARTER_CHANNELS, TASK_STATES, validate_query_product_recommendation

app = FastAPI(title="TMFC050 Recommendation Engine Service")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/rules")
async def rules() -> dict[str, Any]:
    return {
        "taskStates": sorted(TASK_STATES),
        "recommendationTypes": sorted(RECOMMENDATION_TYPES),
        "channels": sorted(STARTER_CHANNELS),
    }


@app.get("/catalog")
async def catalog() -> dict[str, Any]:
    return {
        "count": len(STARTER_CATALOG),
        "items": STARTER_CATALOG,
    }


@app.post("/validate/queryProductRecommendation")
async def validate_query_product_recommendation_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return validate_query_product_recommendation(payload)


@app.post("/recommend/queryProductRecommendation")
async def recommend_query_product_recommendation(payload: dict[str, Any]) -> dict[str, Any]:
    return generate_recommendations(payload)
