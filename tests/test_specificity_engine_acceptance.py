from python.specificity_engine.acceptance import run_acceptance_suite
from python.specificity_engine.demo import run_demo


def test_specificity_acceptance_suite(tmp_path):
    summary = run_acceptance_suite(tmp_path / "acceptance")
    assert summary["passed"]
    assert summary["scenario_count"] == 10
    assert (tmp_path / "acceptance" / "specificity-acceptance.json").exists()


def test_specificity_demo_degrades_repairs_and_replays(tmp_path):
    summary = run_demo(tmp_path / "demo")
    train, relocate, repair = summary["phases"]
    assert train["gsr"] == 1.0
    assert relocate["gsr"] < train["gsr"]
    assert repair["gsr"] == train["gsr"]
    assert relocate["basin"]["action"] != "EXTEND"
    assert repair["basin"]["action"] == "EXTEND"
    assert summary["replay"]["verified"]
    assert (tmp_path / "demo" / "specificity-events.jsonl").exists()
