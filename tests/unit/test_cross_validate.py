import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ml.scripts.cross_validate import _mean_std_ci  # noqa: E402


class TestMeanStdCi:
    def test_single_value_has_zero_spread(self):
        mean, std, lo, hi = _mean_std_ci([0.5])
        assert mean == 0.5
        assert std == 0.0
        assert lo == hi == 0.5

    def test_identical_values_have_zero_spread(self):
        mean, std, lo, hi = _mean_std_ci([0.7, 0.7, 0.7])
        assert mean == 0.7
        assert std == 0.0
        assert lo == hi == 0.7

    def test_ci_is_centered_on_the_mean(self):
        mean, std, lo, hi = _mean_std_ci([0.6, 0.7, 0.8, 0.9])
        assert abs((lo + hi) / 2 - mean) < 1e-9

    def test_wider_spread_produces_wider_ci(self):
        _, _, lo_tight, hi_tight = _mean_std_ci([0.70, 0.71, 0.69, 0.70])
        _, _, lo_wide, hi_wide = _mean_std_ci([0.50, 0.90, 0.60, 0.80])
        assert (hi_wide - lo_wide) > (hi_tight - lo_tight)
