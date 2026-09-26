from satchetak.planning import plan_query
from satchetak.schemas import Sector, Workflow


def test_vegetation_change_query_has_red_nir_contract():
    plan = plan_query("Where has vegetation declined in these fields?")
    assert plan.workflow == Workflow.VEGETATION_CHANGE
    assert plan.sector == Sector.AGRICULTURE
    assert plan.required_bands == ["B04", "B08"]


def test_urban_change_query_has_multispectral_contract():
    plan = plan_query("Show urban development change and cleared land")
    assert plan.workflow == Workflow.GENERIC_LAND_CHANGE
    assert plan.sector == Sector.URBAN_LAND
    assert plan.required_bands == ["B02", "B03", "B04", "B08", "B11", "B12"]
    assert "not proof" in plan.claim_limitations[0]


def test_scene_availability_query_stops_at_observation_evidence():
    plan = plan_query("What satellite observations are available with low cloud?")
    assert plan.workflow == Workflow.OBSERVATION_DISCOVERY
    assert plan.required_bands == []


def test_ambiguous_query_does_not_guess_an_analysis():
    plan = plan_query("Tell me what happened here")
    assert plan.workflow == Workflow.OBSERVATION_DISCOVERY
    assert plan.confidence == "low"


def test_domain_only_query_does_not_run_temporal_analysis():
    plan = plan_query("What is the current land use?")
    assert plan.workflow == Workflow.OBSERVATION_DISCOVERY
    assert plan.sector == Sector.URBAN_LAND
    assert plan.confidence == "medium"
