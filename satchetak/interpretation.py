"""Human-readable reporting assembled only from verified analysis outputs."""
from __future__ import annotations

from typing import Any

from .schemas import ObservationSearchResponse


def build_observation_summary(search: ObservationSearchResponse, workflow: str) -> dict[str, Any]:
    candidates = search.candidates
    qualified = [item for item in candidates if item.quality_state != "rejected_cloud"]
    rejected = len(candidates) - len(qualified)
    start = search.selected.t1.acquisition_time
    end = search.selected.t2.acquisition_time
    intermediate = [item for item in qualified if item.provider_scene_id not in {
        search.selected.t1.provider_scene_id, search.selected.t2.provider_scene_id,
    }]
    support_count = min(2, len(intermediate)) if workflow == "generic_land_change" else 0
    support_label = "observation" if support_count == 1 else "observations"
    return {
        "candidate_count": len(candidates),
        "qualified_count": len(qualified),
        "rejected_count": rejected,
        "selected_span_days": (end - start).days,
        "intermediate_support_count": support_count,
        "selected_dates": [start.date().isoformat(), end.date().isoformat()],
        "candidates": [
            {
                "scene_id": item.provider_scene_id,
                "date": item.acquisition_time.date().isoformat(),
                "cloud_cover": item.cloud_cover,
                "quality_state": item.quality_state,
            }
            for item in candidates
        ],
        "selection_rationale": (
            "The earliest and latest catalogue-qualified observations define the comparison window. "
            + (f"The {support_count} qualified intermediate {support_label} nearest the latest date test whether land-change categories recur."
               if support_count else "No intermediate scene is used by this two-date workflow.")
        ),
        "quality_caveat": "Cloud percentage is scene-level catalogue metadata; the valid-pixel mask determines which AOI pixels enter the calculation.",
    }


def build_interpretation(result: dict[str, Any]) -> dict[str, Any]:
    metrics = result["metrics"]
    evidence = result["evidence"]
    demo = evidence["source_mode"].startswith("demo")
    if result["workflow"] == "generic_land_change":
        changed = metrics["changed_area_ha"]
        clearing = metrics["vegetation_to_bare_area_ha"]
        built = metrics["built_up_like_area_ha"]
        repeated = metrics["repeat_observed_area_ha"]
        latest = metrics["latest_only_area_ha"]
        regions = evidence.get("change_regions", [])
        headline = (
            f"{changed:.2f} ha of connected land-surface change needs attention"
            if changed else "No meaningful connected land-change region passed the screening rules"
        )
        direct_answer = (
            f"The satellite screen found {clearing:.2f} ha of vegetation-to-bare or disturbed-ground candidates and "
            f"{built:.2f} ha of built-up-like candidates. "
            f"Of the total, {repeated:.2f} ha repeated across comparison dates and {latest:.2f} ha appears only in the latest comparison."
            if changed else
            "The available observations did not produce a connected change region above the configured spectral and minimum-area rules."
        )
        evidence_points = [
            f"{metrics['change_region_count']} connected region(s) remained after isolated pixels and regions below {metrics['minimum_region_area_ha']:.2f} ha were removed.",
            f"The largest region covers {metrics['largest_region_area_ha']:.2f} ha" + (f" in the {regions[0]['location']} of the selected area." if regions else "."),
            f"{metrics['temporal_observation_count']} usable dates were checked; repeated means the same category occurred in at least two baseline-relative comparisons.",
        ]
        relevance = []
        if clearing:
            relevance.append("Loss of vegetated cover or exposed/disturbed ground may affect current land cover and should trigger a clearing, harvest, grading, or earthworks check.")
        if built:
            relevance.append("A shift toward hardened-surface signals may affect development context, drainage, or access assumptions, but it does not identify a structure or permitted use.")
        if latest:
            relevance.append("Latest-only regions may be recent genuine change or a transient surface condition; they should not be treated as persistent until another clear observation is available.")
        limitations = [
            "Sentinel-2 screening cannot establish ownership, parcel boundaries, permits, construction type, or encroachment.",
            "Seasonality, soil moisture, shadows, harvest, and earthworks can produce similar spectral responses.",
        ]
        next_action = "Inspect the numbered regions, beginning with repeated change, then compare the latest-only regions against a later clear image and site or planning records."
        confidence = "Demonstration only" if demo else ("Moderate screening confidence" if repeated > 0 and metrics["support_comparison_count"] > 1 else "Preliminary screening confidence")
        confidence_reason = (
            "The values come from simulated pixels and demonstrate the reporting workflow, not this property."
            if demo else
            "Confidence describes the change screen—not the cause. It reflects aligned valid pixels, connected-region filtering, explicit category rules, and multi-date repetition."
        )
    else:
        decline = metrics.get("vegetation_decline_area_ha", metrics.get("vegetation_decline_area_ha_estimate", 0))
        increase = metrics.get("vegetation_increase_area_ha", metrics.get("vegetation_increase_area_ha_estimate", 0))
        headline = f"Vegetation activity declined across {decline:.2f} ha and increased across {increase:.2f} ha"
        direct_answer = (
            f"Mean NDVI moved from {metrics['mean_ndvi_t1']:.3f} to {metrics['mean_ndvi_t2']:.3f}. "
            "The result measures vegetation-response change between two dates; it does not diagnose why it changed."
        )
        evidence_points = [
            f"{metrics['valid_pixel_count']} mutually valid pixels were used.",
            f"{metrics['decline_share_pct']:.1f}% crossed the decline threshold and {metrics['increase_share_pct']:.1f}% crossed the increase threshold.",
            f"Latest-date median NDVI is {metrics['ndvi_t2_median']:.3f}, with P10/P90 of {metrics['ndvi_t2_p10']:.3f}/{metrics['ndvi_t2_p90']:.3f}.",
        ]
        relevance = [
            "Declining regions deserve field inspection and comparison with crop stage, harvest, irrigation, and recent management history.",
            "Increasing regions indicate stronger greenness response, not verified crop health, productivity, or yield.",
        ]
        limitations = [
            "Two dates cannot separate normal crop seasonality from persistent decline.",
            "NDVI alone cannot diagnose disease, nutrients, water stress, soil quality, or yield loss.",
        ]
        next_action = "Inspect the strongest decline areas and compare multiple observations from the same crop stage before making an agricultural decision."
        confidence = "Demonstration only" if demo else "Preliminary two-date evidence"
        confidence_reason = (
            "The values come from simulated pixels and demonstrate the reporting workflow, not this field."
            if demo else
            "The calculation uses aligned, mutually valid Red/NIR pixels and explicit thresholds, but only two endpoint dates."
        )
    return {
        "headline": headline,
        "direct_answer": direct_answer,
        "confidence": confidence,
        "confidence_reason": confidence_reason,
        "evidence_points": evidence_points,
        "decision_relevance": relevance,
        "limitations": limitations,
        "next_action": next_action,
        "source": "deterministic_verified_evidence",
    }
