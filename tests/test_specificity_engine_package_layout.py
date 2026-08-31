import specificity_engine
from python import specificity_engine as canonical


def test_top_level_package_exports_canonical_contracts():
    assert specificity_engine.MeasurementReceipt is canonical.MeasurementReceipt
    assert specificity_engine.SpecificityLedger is canonical.SpecificityLedger
    assert specificity_engine.DebtPosture is canonical.DebtPosture
