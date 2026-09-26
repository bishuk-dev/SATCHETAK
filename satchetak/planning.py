from __future__ import annotations

import re

from .schemas import QueryPlan, Sector, Workflow

OBSERVATION_TERMS = {"available", "availability", "cloud", "image", "imagery", "latest", "observation", "scene", "satellite"}
VEGETATION_TERMS = {"agriculture", "agricultural", "farming", "crops", "crop", "farm", "field", "green", "ndvi", "plant", "vegetation", "soil", "irrigation"}
LAND_TERMS = {"building", "buildings", "built", "cleared", "construction", "development", "expansion", "land", "urban"}
CHANGE_TERMS = {"change", "changed", "changing", "decline", "declined", "decrease", "decreased", "difference", "increase", "increased", "loss", "lost", "new"}


def _matches(words: set[str], vocabulary: set[str]) -> list[str]:
    return sorted(words & vocabulary)


def plan_query(query: str) -> QueryPlan:
    words = set(re.findall(r"[a-z]+", query.lower()))
    observation = _matches(words, OBSERVATION_TERMS)
    vegetation = _matches(words, VEGETATION_TERMS)
    land = _matches(words, LAND_TERMS)
    change = _matches(words, CHANGE_TERMS)

    purchase = _matches(words, {"buy", "buying", "purchase", "investment", "invest", "worth", "suitable", "suitability", "commercial", "feasibility"})
    if purchase:
        agriculture = bool(vegetation)
        return QueryPlan(
            query=query, sector=Sector.AGRICULTURE if agriculture else Sector.URBAN_LAND,
            workflow=Workflow.VEGETATION_CHANGE if agriculture else Workflow.GENERIC_LAND_CHANGE,
            assessment_purpose="agriculture_purchase" if agriculture else "development_purchase",
            confidence="medium", recognized_terms=purchase + vegetation + land,
            required_bands=["B04", "B08"] if agriculture else ["B02", "B03", "B04", "B08", "B11", "B12"],
            requested_outputs=["change_evidence", "preliminary_land_screening", "missing_checks", "next_steps"],
            claim_limitations=["Satellite change alone cannot establish suitability, ownership, market value, or a buy/no-buy recommendation."],
            rationale="Purchase or suitability intent triggers a preliminary land screen with explicit due-diligence gaps.",
        )

    if vegetation and words & {"health", "condition", "monitor", "assess", "analyze", "analyse"}:
        change = change or ["condition"]

    if vegetation and change:
        return QueryPlan(
            query=query, sector=Sector.AGRICULTURE, workflow=Workflow.VEGETATION_CHANGE,
            confidence="high", recognized_terms=vegetation + change, required_bands=["B04", "B08"],
            requested_outputs=["ndvi_t1", "ndvi_t2", "delta_ndvi", "change_area", "evidence"],
            claim_limitations=["No disease, nutrient, yield, or causal diagnosis."],
            rationale="Vegetation terms plus temporal-change terms require paired Red/NIR analysis.",
        )
    if land and change:
        return QueryPlan(
            query=query, sector=Sector.URBAN_LAND, workflow=Workflow.GENERIC_LAND_CHANGE,
            confidence="high", recognized_terms=land + change, required_bands=["B02", "B03", "B04", "B08", "B11", "B12"],
            requested_outputs=["change_categories", "change_regions", "area_by_category", "evidence"],
            claim_limitations=["Spectral categories are screening candidates, not proof of construction type or encroachment."],
            rationale="Land-development terms plus temporal-change terms require visible, NIR, and SWIR change screening.",
        )
    if observation or not (vegetation or land):
        terms = observation or sorted(words)[:5]
        return QueryPlan(
            query=query, sector=Sector.AGRICULTURE, workflow=Workflow.OBSERVATION_DISCOVERY,
            confidence="high" if observation else "low", recognized_terms=terms, required_bands=[],
            requested_outputs=["candidate_scenes", "quality_filter", "selected_t1_t2"],
            claim_limitations=["Catalogue metadata alone does not support a land-change claim."],
            rationale="The request asks for observations, or does not provide enough supported domain intent for analysis.",
        )
    sector = Sector.AGRICULTURE if vegetation else Sector.URBAN_LAND
    return QueryPlan(
        query=query, sector=sector, workflow=Workflow.OBSERVATION_DISCOVERY, confidence="medium",
        recognized_terms=vegetation or land,
        required_bands=[], requested_outputs=["candidate_scenes", "selected_observation"],
        claim_limitations=["A temporal-change result requires explicit comparison intent and two observations."],
        rationale="A domain was recognized, but no supported analysis intent was explicit; discovery is the safe fallback.",
    )
