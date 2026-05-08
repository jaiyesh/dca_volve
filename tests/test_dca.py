"""
Failing tests for DCA math core (utils/dca.py).
Run BEFORE implementation — all should fail with ImportError or AssertionError.
"""
import sys
sys.path.insert(0, '/Users/jc116117/Desktop/jc/ED/webinar/codebase')

import numpy as np
import pandas as pd


def test_rate_functions_at_t0():
    """Rate functions must return qi exactly at t=0 (identity check)."""
    from utils.dca import exponential_q, hyperbolic_q, harmonic_q
    assert abs(exponential_q(np.array([0.0]), 1000, 0.01)[0] - 1000.0) < 0.01
    assert abs(hyperbolic_q(np.array([0.0]), 1000, 0.01, 0.5)[0] - 1000.0) < 0.01
    assert abs(harmonic_q(np.array([0.0]), 1000, 0.01)[0] - 1000.0) < 0.01


def test_harmonic_q_at_t100():
    """Harmonic q(100) with Di=0.01 → 1000/(1+1.0) = 500.0."""
    from utils.dca import harmonic_q
    assert abs(harmonic_q(np.array([100.0]), 1000, 0.01)[0] - 500.0) < 0.01


def test_exponential_q_at_t100():
    """Exponential q(100) with Di=0.01 → 1000*exp(-1.0) ≈ 367.88."""
    from utils.dca import exponential_q
    expected = 1000 * np.exp(-1.0)
    assert abs(exponential_q(np.array([100.0]), 1000, 0.01)[0] - expected) < 0.01


def test_eur_finite_positive_exponential():
    from utils.dca import calculate_eur
    eur = calculate_eur('exponential', 1000, 0.01, 0.0, q_aband=1.0)
    assert np.isfinite(eur) and eur > 0, f'Exponential EUR={eur}'


def test_eur_finite_positive_harmonic():
    from utils.dca import calculate_eur
    eur = calculate_eur('harmonic', 1000, 0.01, 1.0, q_aband=1.0)
    assert np.isfinite(eur) and eur > 0, f'Harmonic EUR={eur}'


def test_eur_finite_positive_hyperbolic():
    from utils.dca import calculate_eur
    eur = calculate_eur('hyperbolic', 1000, 0.01, 0.5, q_aband=1.0)
    assert np.isfinite(eur) and eur > 0, f'Hyperbolic EUR={eur}'


def test_eur_near_harmonic_guard():
    """b=0.99 must trigger harmonic guard — result must be finite (not inf)."""
    from utils.dca import calculate_eur
    eur = calculate_eur('hyperbolic', 1000, 0.01, 0.99, q_aband=1.0)
    assert np.isfinite(eur) and eur > 0, f'Near-harmonic EUR={eur}'


def test_eur_hyperbolic_exceeds_exponential():
    """Physically: hyperbolic declines slower → higher EUR than exponential."""
    from utils.dca import calculate_eur
    eur_exp = calculate_eur('exponential', 1000, 0.01, 0.0, q_aband=1.0)
    eur_hyp = calculate_eur('hyperbolic', 1000, 0.01, 0.5, q_aband=1.0)
    assert eur_hyp > eur_exp, f'Hyperbolic EUR={eur_hyp} should exceed exponential EUR={eur_exp}'


def test_fit_arps_returns_correct_keys():
    from utils.dca import fit_arps
    dates = pd.date_range('2009-01-01', periods=300, freq='D')
    t = np.arange(300, dtype=float)
    q_syn = 2000 * np.exp(-0.005 * t)
    df_syn = pd.DataFrame({'DATEPRD': dates, 'BORE_OIL_VOL': q_syn, 'ON_STREAM_HRS': 24.0})
    result = fit_arps(df_syn, model='exponential')
    assert 'qi' in result and 'Di' in result and 'r2' in result and 'model' in result


def test_fit_arps_r2_high_on_synthetic():
    from utils.dca import fit_arps
    dates = pd.date_range('2009-01-01', periods=300, freq='D')
    t = np.arange(300, dtype=float)
    q_syn = 2000 * np.exp(-0.005 * t)
    df_syn = pd.DataFrame({'DATEPRD': dates, 'BORE_OIL_VOL': q_syn, 'ON_STREAM_HRS': 24.0})
    result = fit_arps(df_syn, model='exponential')
    assert result['r2'] > 0.95, f'R2={result["r2"]} (expected > 0.95 for synthetic data)'


def test_forecast_arps_returns_calendar_dates():
    from utils.dca import fit_arps, forecast_arps
    dates = pd.date_range('2009-01-01', periods=300, freq='D')
    t = np.arange(300, dtype=float)
    q_syn = 2000 * np.exp(-0.005 * t)
    df_syn = pd.DataFrame({'DATEPRD': dates, 'BORE_OIL_VOL': q_syn, 'ON_STREAM_HRS': 24.0})
    result = fit_arps(df_syn, model='exponential')
    fc = forecast_arps(result, forecast_months=12, q_aband=1.0)
    assert 'date' in fc.columns and 'q' in fc.columns
    assert pd.api.types.is_datetime64_any_dtype(fc['date'])
    assert (fc['q'] >= 1.0).all()


def test_get_latex_nonempty():
    from utils.dca import get_latex_equation
    for m in ['exponential', 'hyperbolic', 'harmonic']:
        latex = get_latex_equation(m, 1000, 0.01, 0.5)
        assert len(latex) > 0, f'Empty LaTeX for {m}'


if __name__ == '__main__':
    tests = [
        test_rate_functions_at_t0,
        test_harmonic_q_at_t100,
        test_exponential_q_at_t100,
        test_eur_finite_positive_exponential,
        test_eur_finite_positive_harmonic,
        test_eur_finite_positive_hyperbolic,
        test_eur_near_harmonic_guard,
        test_eur_hyperbolic_exceeds_exponential,
        test_fit_arps_returns_correct_keys,
        test_fit_arps_r2_high_on_synthetic,
        test_forecast_arps_returns_calendar_dates,
        test_get_latex_nonempty,
    ]
    failed = 0
    for test in tests:
        try:
            test()
            print(f'  PASS: {test.__name__}')
        except Exception as e:
            print(f'  FAIL: {test.__name__} — {e}')
            failed += 1
    print(f'\n{len(tests) - failed}/{len(tests)} tests passed')
    if failed > 0:
        sys.exit(1)
