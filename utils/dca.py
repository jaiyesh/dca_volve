"""
DCA math core — Arps decline curve analysis.

Pure scipy/numpy/pandas. Zero Streamlit dependency.
Exports: exponential_q, hyperbolic_q, harmonic_q, fit_arps, forecast_arps,
         calculate_eur, get_latex_equation
"""
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit, OptimizeWarning
import warnings
from typing import Literal

ModelType = Literal["exponential", "hyperbolic", "harmonic"]

# ── Rate functions q(t) ────────────────────────────────────────────────────────

def exponential_q(t: np.ndarray, qi: float, Di: float) -> np.ndarray:
    """q(t) = qi * exp(-Di * t). t in days."""
    return qi * np.exp(-Di * t)


def hyperbolic_q(t: np.ndarray, qi: float, Di: float, b: float) -> np.ndarray:
    """q(t) = qi / (1 + b*Di*t)^(1/b). t in days. b in (0, 1) exclusive."""
    return qi / np.power(1.0 + b * Di * t, 1.0 / b)


def harmonic_q(t: np.ndarray, qi: float, Di: float) -> np.ndarray:
    """q(t) = qi / (1 + Di*t). Special case b=1. t in days."""
    return qi / (1.0 + Di * t)


# ── Cumulative Np (volume from t0 to t_end) ────────────────────────────────────

def _exponential_np(qi: float, Di: float, t0: float, t_end: float) -> float:
    """Np for exponential decline from t0 to t_end."""
    return (qi / Di) * (np.exp(-Di * t0) - np.exp(-Di * t_end))


def _hyperbolic_np(qi: float, Di: float, b: float, t0: float, t_end: float) -> float:
    """Np for hyperbolic decline (0 < b < 1, b ≠ 1) from t0 to t_end."""
    q0 = hyperbolic_q(np.array([t0]), qi, Di, b)[0]
    q_end = hyperbolic_q(np.array([t_end]), qi, Di, b)[0]
    return (qi ** b / ((1.0 - b) * Di)) * (q0 ** (1.0 - b) - q_end ** (1.0 - b))


def _harmonic_np(qi: float, Di: float, t0: float, t_end: float) -> float:
    """Np for harmonic decline (b=1) from t0 to t_end."""
    q0 = harmonic_q(np.array([t0]), qi, Di)[0]
    q_end = harmonic_q(np.array([t_end]), qi, Di)[0]
    return (qi / Di) * np.log(q0 / q_end)


# ── EUR (integrates to economic abandonment rate, never to infinite time) ──────

def calculate_eur(
    model: ModelType,
    qi: float,
    Di: float,
    b: float,
    q_aband: float = 1.0,
) -> float:
    """
    EUR to economic limit q_aband (Sm3/day).
    Returns EUR in Sm3. Never returns inf or nan.

    Harmonic guard: abs(b-1.0) < 0.01 -> use harmonic branch to prevent
    singularity in (1-b) denominator of hyperbolic Np formula.
    """
    if q_aband >= qi:
        return 0.0

    # Harmonic guard — prevents singularity at b≈1 in hyperbolic formula
    effective_model = model
    if model == "hyperbolic" and abs(b - 1.0) < 0.01:
        effective_model = "harmonic"

    if effective_model == "exponential":
        # Solve qi*exp(-Di*t) = q_aband => t = ln(qi/q_aband)/Di
        t_aband = np.log(qi / q_aband) / Di
        return _exponential_np(qi, Di, 0.0, t_aband)

    elif effective_model == "harmonic":
        # Solve qi/(1+Di*t) = q_aband => t = (qi/q_aband - 1)/Di
        t_aband = (qi / q_aband - 1.0) / Di
        return _harmonic_np(qi, Di, 0.0, t_aband)

    else:  # hyperbolic (b not near 1)
        # Solve qi/(1+b*Di*t)^(1/b) = q_aband => t = ((qi/q_aband)^b - 1)/(b*Di)
        t_aband = ((qi / q_aband) ** b - 1.0) / (b * Di)
        return _hyperbolic_np(qi, Di, b, 0.0, t_aband)


# ── curve_fit wrapper ─────────────────────────────────────────────────────────

def fit_arps(
    df: pd.DataFrame,
    model: ModelType = "hyperbolic",
) -> dict:
    """
    Fit an Arps decline curve to df (must have DATEPRD and BORE_OIL_VOL columns,
    already filtered to ON_STREAM_HRS > 0 and the user's date range).

    Returns dict: {qi, Di, b, r2, rmse, model, t0, warning}
    Raises ValueError on convergence failure (caller displays with st.error).

    p0 is strictly inside bounds per scipy issue #19180:
      qi_0 = first_rate * 0.9 (not exact value), Di_0 = 0.01, b_0 = 0.5
    method='trf' required when bounds are active.
    """
    df = df.dropna(subset=["BORE_OIL_VOL"]).copy()
    df = df[df["BORE_OIL_VOL"] > 0]
    if len(df) < 5:
        raise ValueError("Fewer than 5 producing data points in selected range.")

    t0 = df["DATEPRD"].min()
    t = (df["DATEPRD"] - t0).dt.days.values.astype(float)
    q = df["BORE_OIL_VOL"].values.astype(float)

    # p0 strictly inside bounds (not at boundary) — scipy issue #19180
    qi_guess = q[0] * 0.9
    Di_guess = 0.01
    b_guess = 0.5

    fit_warning = None

    try:
        if model == "exponential":
            popt, _ = curve_fit(
                exponential_q,
                t,
                q,
                p0=[qi_guess, Di_guess],
                bounds=([0, 1e-5], [qi_guess * 3, 1.0]),
                method="trf",
                maxfev=10000,
            )
            qi_fit, Di_fit, b_fit = popt[0], popt[1], 0.0
            q_pred = exponential_q(t, qi_fit, Di_fit)

        elif model == "harmonic":
            popt, _ = curve_fit(
                harmonic_q,
                t,
                q,
                p0=[qi_guess, Di_guess],
                bounds=([0, 1e-5], [qi_guess * 3, 1.0]),
                method="trf",
                maxfev=10000,
            )
            qi_fit, Di_fit, b_fit = popt[0], popt[1], 1.0
            q_pred = harmonic_q(t, qi_fit, Di_fit)

        else:  # hyperbolic (default)
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                popt, _ = curve_fit(
                    hyperbolic_q,
                    t,
                    q,
                    p0=[qi_guess, Di_guess, b_guess],
                    bounds=([0, 1e-5, 0.0], [qi_guess * 3, 1.0, 1.0]),
                    method="trf",
                    maxfev=10000,
                )
                if w:
                    fit_warning = str(w[-1].message)
            qi_fit, Di_fit, b_fit = popt
            q_pred = hyperbolic_q(t, qi_fit, Di_fit, b_fit)

    except (RuntimeError, OptimizeWarning) as exc:
        raise ValueError(f"Arps curve_fit did not converge: {exc}") from exc

    ss_res = float(np.sum((q - q_pred) ** 2))
    ss_tot = float(np.sum((q - q.mean()) ** 2))
    r2 = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else 0.0
    rmse = float(np.sqrt(ss_res / len(q)))

    return {
        "qi": float(qi_fit),
        "Di": float(Di_fit),
        "b": float(b_fit),
        "r2": round(r2, 4),
        "rmse": round(rmse, 2),
        "model": model,
        "t0": t0,
        "warning": fit_warning,
    }


# ── Forecast generation ───────────────────────────────────────────────────────

def forecast_arps(
    fit_result: dict,
    forecast_months: int = 120,
    q_aband: float = 1.0,
) -> pd.DataFrame:
    """
    Generate forecast DataFrame with calendar dates.
    Extends from fit_result['t0'] for forecast_months months.
    Stops early if q drops below q_aband.

    Returns DataFrame with columns:
      date (pd.Timestamp) — calendar dates, NOT integer day offsets
      q    (float)        — rate in Sm3/day
    """
    qi = fit_result["qi"]
    Di = fit_result["Di"]
    b = fit_result["b"]
    model = fit_result["model"]
    t0 = fit_result["t0"]

    # Daily resolution, capped at forecast_months * 30 days
    n_days = forecast_months * 30
    t_arr = np.arange(0, n_days + 1, dtype=float)

    # Harmonic guard mirrors calculate_eur()
    effective_model = model
    if model == "hyperbolic" and abs(b - 1.0) < 0.01:
        effective_model = "harmonic"

    if effective_model == "exponential":
        q_arr = exponential_q(t_arr, qi, Di)
    elif effective_model == "harmonic":
        q_arr = harmonic_q(t_arr, qi, Di)
    else:
        q_arr = hyperbolic_q(t_arr, qi, Di, b)

    # Truncate at economic limit
    mask = q_arr >= q_aband
    t_arr = t_arr[mask]
    q_arr = q_arr[mask]

    # Calendar-date x-axis — pd.DatetimeIndex, not integer days
    dates = pd.to_datetime(t0) + pd.to_timedelta(t_arr, unit="D")
    return pd.DataFrame({"date": dates, "q": q_arr})


# ── LaTeX equation display ────────────────────────────────────────────────────

def get_latex_equation(model: ModelType, qi: float, Di: float, b: float) -> str:
    """
    Return a LaTeX string of the active Arps equation with current parameter values.
    Used by st.latex() in the DCA Forecast page.
    """
    qi_str = f"{qi:.1f}"
    Di_str = f"{Di:.5f}"
    b_str = f"{b:.2f}"

    if model == "exponential":
        return r"q(t) = " + qi_str + r"\, e^{-" + Di_str + r"\, t}"
    elif model == "harmonic":
        return r"q(t) = \dfrac{" + qi_str + r"}{1 + " + Di_str + r"\, t}"
    else:  # hyperbolic
        exp_str = f"1/{b_str}"
        return (
            r"q(t) = \dfrac{" + qi_str + r"}{"
            r"\left(1 + " + b_str + r"\cdot " + Di_str + r"\, t\right)^{" + exp_str + r"}}"
        )
