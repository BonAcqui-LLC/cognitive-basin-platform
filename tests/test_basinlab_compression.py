"""
Verified compression tests for BasinLab.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from python.basinlab.compression import CompressedTrajectory, FullTrajectoryRecord, VerifiedCompression


def _validator(full: FullTrajectoryRecord, compressed: CompressedTrajectory) -> bool:
    return (
        full.final_epistemic == compressed.final_epistemic
        and full.replay_references == compressed.replay_references
        and set(full.decisive_claims) == set(compressed.decisive_claims)
    )


def _full_record() -> FullTrajectoryRecord:
    return FullTrajectoryRecord(
        purpose="Bridge inspection",
        decisive_claims=["claim-1"],
        evidence_links={"claim-1": ["inspection-report"], "claim-2": ["secondary-note"]},
        contradictory_evidence={"claim-2": ["crack-scan"]},
        failures_changed_route=["initial-path-failed"],
        scar_ids=["scar-1"],
        recovery_decisions=["route-1:success"],
        commit_decision="commit-1",
        replay_references={"session_id": "session-1", "checkpoint": "hash-1"},
        final_epistemic="UNRESOLVED",
        uncertainty=["Need follow-up scan"],
    )


def test_compression_retains_required_fields():
    compressed = VerifiedCompression(_validator).compress(_full_record())
    assert compressed.decisive_claims == ["claim-1"]
    assert compressed.evidence_links["claim-1"] == ["inspection-report"]
    assert compressed.contradictory_evidence["claim-2"] == ["crack-scan"]
    assert compressed.scar_ids == ["scar-1"]
    assert compressed.recovery_decisions == ["route-1:success"]
    assert compressed.commit_decision == "commit-1"


def test_compression_rejects_missing_decisive_evidence():
    full = _full_record()
    full.evidence_links["claim-1"] = []
    with pytest.raises(ValueError, match="decisive evidence lost"):
        VerifiedCompression(_validator).compress(full)


def test_compression_rejects_missing_replay_validity():
    def bad_validator(_full: FullTrajectoryRecord, _compressed: CompressedTrajectory) -> bool:
        return False

    with pytest.raises(ValueError, match="replay no longer reconstructs"):
        VerifiedCompression(bad_validator).compress(_full_record())


def test_compression_rejects_uncertainty_converted_to_support():
    full = _full_record()
    full.final_epistemic = "SUPPORTED"
    with pytest.raises(ValueError, match="uncertainty converted into support"):
        VerifiedCompression(_validator).compress(full)


def test_compression_rejects_incomplete_provenance():
    full = _full_record()
    full.provenance_complete = False
    with pytest.raises(ValueError, match="provenance becomes incomplete"):
        VerifiedCompression(_validator).compress(full)


def test_compressed_and_full_records_match_governed_result():
    full = _full_record()
    compressed = VerifiedCompression(_validator).compress(full)
    assert compressed.final_epistemic == full.final_epistemic
    assert compressed.replay_references == full.replay_references
    assert compressed.digest
