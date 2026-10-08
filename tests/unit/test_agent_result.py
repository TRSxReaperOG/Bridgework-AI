import json

import pytest
from pydantic import ValidationError

from bridgework.schemas import AgentResult, AgentStatus


def test_defaults_describe_an_empty_ok_result():
    r = AgentResult()
    assert r.status is AgentStatus.OK
    assert r.result == {}
    assert r.confidence == 0.0
    assert r.sources == []
    assert r.errors == []


def test_defaults_are_not_shared_between_instances():
    a, b = AgentResult(), AgentResult()
    a.sources.append("https://example.com")
    assert b.sources == []


@pytest.mark.parametrize("confidence", [0.0, 0.5, 1.0])
def test_confidence_accepts_values_in_range(confidence):
    assert AgentResult(confidence=confidence).confidence == confidence


@pytest.mark.parametrize("confidence", [-0.01, 1.01, float("nan")])
def test_confidence_rejects_values_out_of_range(confidence):
    with pytest.raises(ValidationError):
        AgentResult(confidence=confidence)


def test_unknown_status_is_rejected():
    with pytest.raises(ValidationError):
        AgentResult(status="maybe")


def test_unknown_fields_are_rejected():
    with pytest.raises(ValidationError):
        AgentResult(confidense=0.9)


def test_error_status_requires_an_error_message():
    with pytest.raises(ValidationError):
        AgentResult(status=AgentStatus.ERROR)
    r = AgentResult(status=AgentStatus.ERROR, errors=["search API timed out"])
    assert r.errors == ["search API timed out"]


def test_no_evidence_status_cannot_have_sources():
    with pytest.raises(ValidationError):
        AgentResult(status=AgentStatus.NO_EVIDENCE, sources=["https://example.com"])
    r = AgentResult(status=AgentStatus.NO_EVIDENCE, result={"queries_tried": ["a", "b"]})
    assert r.confidence == 0.0


def test_json_round_trip_preserves_everything():
    original = AgentResult(
        status=AgentStatus.OK,
        result={"tiers": {"1": 2, "2": 1}, "queries_tried": ["direct", "broader"]},
        confidence=0.72,
        sources=["https://docs.example.com/a", "https://arxiv.org/abs/1"],
        errors=["one source failed to load"],
    )
    restored = AgentResult.model_validate_json(original.model_dump_json())
    assert restored == original


def test_status_serializes_as_plain_string():
    payload = json.loads(AgentResult(status=AgentStatus.NO_EVIDENCE).model_dump_json())
    assert payload["status"] == "no_evidence"
    assert set(payload) == {"status", "result", "confidence", "sources", "errors"}
