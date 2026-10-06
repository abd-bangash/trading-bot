import unittest
import numpy as np
from tradeproof import analysis as A
from tradeproof.report import build_report


class T(unittest.TestCase):
    def test_max_dd(self):
        self.assertAlmostEqual(A.max_drawdown(np.array([10., -20., 5.]), 100), 20 / 110, places=6)

    def test_deflation_lowers_confidence(self):
        pnl = np.random.default_rng(0).normal(20, 100, 200)
        self.assertGreater(A.deflated_sharpe(pnl, 1), A.deflated_sharpe(pnl, 500))

    def test_noise_not_pass(self):
        pnl = np.random.default_rng(3).normal(0, 100, 200)
        self.assertNotEqual(build_report(pnl, 100000, 50)[0], "PASS")

    def test_real_edge_pass(self):
        r = np.random.default_rng(2)
        pnl = np.where(r.random(400) < .6, 300., -200.) + r.normal(0, 20, 400)
        self.assertEqual(build_report(pnl, 100000, 1)[0], "PASS")

    def test_prop_sim_bounds(self):
        r = A.prop_firm_sim(np.array([100., -100.] * 50), 10000, 0.05, 0.05, 0.1, runs=200)
        self.assertAlmostEqual(sum(r.values()), 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
