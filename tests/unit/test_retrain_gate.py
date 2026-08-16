import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ml.scripts.retrain_gate import _should_promote  # noqa: E402


class TestShouldPromote:
    def test_identical_performance_is_promoted(self):
        assert _should_promote(candidate_f1=0.80, incumbent_f1=0.80, tolerance=0.02) is True

    def test_improved_candidate_is_promoted(self):
        assert _should_promote(candidate_f1=0.85, incumbent_f1=0.80, tolerance=0.02) is True

    def test_regression_within_tolerance_is_promoted(self):
        assert _should_promote(candidate_f1=0.79, incumbent_f1=0.80, tolerance=0.02) is True

    def test_regression_beyond_tolerance_is_rejected(self):
        assert _should_promote(candidate_f1=0.70, incumbent_f1=0.80, tolerance=0.02) is False

    def test_zero_tolerance_rejects_any_regression(self):
        assert _should_promote(candidate_f1=0.799, incumbent_f1=0.80, tolerance=0.0) is False
