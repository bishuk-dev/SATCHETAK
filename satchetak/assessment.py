"""Deterministic decision support; satellite evidence never becomes a purchase verdict."""
from typing import Any


def build_assessment(result: dict[str, Any], purpose: str) -> dict[str, Any]:
    demo = result["evidence"]["source_mode"].startswith("demo")
    metrics = result["metrics"]
    if purpose == "agriculture_purchase":
        findings = [
            f"Mean NDVI: {metrics['mean_ndvi_t1']:.3f} at T1 and {metrics['mean_ndvi_t2']:.3f} at T2.",
            f"Vegetation decline affects {metrics['decline_share_pct']:.1f}% of mutually valid pixels at the configured threshold.",
            "Two observations cannot distinguish seasonal cropping, harvest, irrigation effects, or persistent degradation.",
        ]
        checks = [
            ("Soil", "Obtain georeferenced tests for texture, depth, pH, salinity, and organic matter."),
            ("Water", "Verify irrigation access, lawful supply, seasonal reliability, and water quality."),
            ("Terrain", "Measure slope, drainage, and machinery access using a qualified elevation survey."),
            ("Climate and crop", "Compare multi-year rainfall and temperature with the intended crop and planting calendar."),
            ("Seasonality", "Review multiple growing seasons of quality-filtered observations and field history."),
        ]
    else:
        findings = [
            f"Meaningful connected change regions cover {metrics['changed_area_ha']:.2f} ha ({metrics['changed_share_pct']:.1f}%) of {metrics['valid_area_ha']:.2f} ha of valid overlap.",
            f"Category screen: {metrics['vegetation_to_bare_area_ha']:.2f} ha vegetation-to-bare/disturbed candidate; {metrics['built_up_like_area_ha']:.2f} ha built-up-like candidate; {metrics['other_change_area_ha']:.2f} ha other change.",
            f"Temporal check: {metrics['repeat_observed_area_ha']:.2f} ha showed the same category in multiple comparison dates; {metrics['latest_only_area_ha']:.2f} ha appears only in the latest comparison.",
            f"{metrics['change_region_count']} connected regions passed the minimum size rule; the largest covers {metrics['largest_region_area_ha']:.2f} ha.",
            "These categories do not establish construction type, developable area, permitted use, or parcel boundaries.",
        ]
        checks = [
            ("Permitted use", "Verify zoning, land conversion permissions, and applicable development restrictions."),
            ("Access and services", "Verify legal road access and the availability and cost of utilities."),
            ("Ground conditions", "Obtain a topographic survey and geotechnical investigation for the proposed use."),
        ]
    checks += [
        ("Title and boundaries", "Verify ownership, encumbrances, cadastral boundaries, and physical access with local records."),
        ("Economics", "Compare asking price, local transactions, operating costs, and intended-use revenue using verified records."),
    ]
    return {
        "purpose": purpose,
        "status": "demo_only" if demo else "insufficient_evidence",
        "conclusion": "Demonstration only: simulated pixels cannot assess this property's purchase suitability."
        if demo else (
            "Satellite screening classified measurable surface-change candidates and tested whether they recur across usable dates. "
            "Use the highlighted regions as inspection leads, not as proof of construction, legality, or purchase suitability."
        ),
        "findings": findings,
        "missing_checks": [{"name": name, "status": "not_assessed", "action": action} for name, action in checks],
        "next_steps": ["Run live observations for the exact area and relevant dates." if demo else "Inspect the dated evidence and flagged regions on site.",
                       "Collect the missing checks before making a purchase decision."],
    }
