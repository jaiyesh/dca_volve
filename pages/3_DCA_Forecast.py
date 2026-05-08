import streamlit as st
import pandas as pd
from utils.data import load_data, filter_by_date, get_sidebar_kpis
from utils.dca import fit_arps, forecast_arps, calculate_eur, get_latex_equation
from utils.charts import build_dca_chart

st.set_page_config(page_title="DCA Forecast — Volve DCA", layout="wide")

# ── Load data ──────────────────────────────────────────────────────────────────
df = load_data()
kpis = get_sidebar_kpis(df)

# ── Session state initialization (MUST run before any widget) ─────────────────
_ss_defaults = {
    "dca_qi": 500.0,
    "dca_Di": 0.01,
    "dca_b": 0.5,
    "dca_fitted": False,
    "dca_r2": None,
    "dca_rmse": None,
    "dca_model": "hyperbolic",
    "dca_t0": None,
    "dca_fit_error": None,
}
for _k, _v in _ss_defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ── Sidebar controls ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Volve DCA Dashboard")
    st.caption("Well: **15/9-F-12**")
    st.caption(f"Period: {kpis['date_start']} – {kpis['date_end']}")
    st.metric("Total Oil", f"{kpis['total_oil_mmsm3']:.3f} MSm³")

    st.divider()
    st.subheader("Fitting Window")

    date_min = df["DATEPRD"].min().date()
    date_max = df["DATEPRD"].max().date()

    # Default fit window: Jan 2009 – Dec 2012 (Volve clean decline period)
    default_start = pd.Timestamp("2009-01-01").date()
    default_end = pd.Timestamp("2012-12-31").date()

    start_date = st.date_input(
        "Start date", value=default_start,
        min_value=date_min, max_value=date_max,
        key="dca_start_date",
    )
    end_date = st.date_input(
        "End date", value=default_end,
        min_value=date_min, max_value=date_max,
        key="dca_end_date",
    )

    st.divider()
    st.subheader("Arps Model")
    model = st.radio(
        "Decline model",
        options=["exponential", "hyperbolic", "harmonic"],
        index=1,
        key="dca_model_radio",
        captions=["b = 0, fastest", "0 < b < 1, typical", "b = 1, slowest"],
    )

    st.divider()
    # Auto-Fit button — triggers scipy curve_fit ONLY when clicked
    auto_fit_clicked = st.button("Auto-Fit", type="primary", use_container_width=True)

    if auto_fit_clicked:
        df_window = filter_by_date(df, start_date, end_date)
        if len(df_window) < 5:
            st.session_state["dca_fit_error"] = "Select a date range with at least 5 producing days."
        else:
            try:
                result = fit_arps(df_window, model=model)
                # Write fitted params to session_state — sliders will read these on next render
                st.session_state["dca_qi"] = result["qi"]
                st.session_state["dca_Di"] = result["Di"]
                st.session_state["dca_b"] = result["b"]
                st.session_state["dca_r2"] = result["r2"]
                st.session_state["dca_rmse"] = result["rmse"]
                st.session_state["dca_model"] = result["model"]
                st.session_state["dca_t0"] = result["t0"]
                st.session_state["dca_fitted"] = True
                st.session_state["dca_fit_error"] = None
            except ValueError as e:
                st.session_state["dca_fit_error"] = str(e)
                st.session_state["dca_fitted"] = False

    st.divider()
    st.subheader("Manual Tuning")

    # Sliders — key-only binding (NEVER pass value= here — StreamlitAPIException)
    st.slider("qi — Initial Rate (Sm³/day)", 1.0, 10000.0, step=10.0, key="dca_qi")
    st.slider("Di — Nominal Decline (1/day)", 0.00001, 0.5, step=0.0001, format="%.5f", key="dca_Di")
    st.slider("b — Hyperbolic Exponent", 0.0, 1.0, step=0.05, key="dca_b")

    st.divider()
    st.subheader("Forecast Settings")
    forecast_months = st.slider("Forecast Horizon (months)", 12, 360, value=120, step=12)
    q_aband = st.slider("Abandonment Rate (Sm³/day)", 0.1, 100.0, value=1.0, step=0.1)

    # EUR — computed from current slider values (runs on every rerun)
    eur_val = calculate_eur(
        model=model,
        qi=st.session_state["dca_qi"],
        Di=st.session_state["dca_Di"],
        b=st.session_state["dca_b"],
        q_aband=q_aband,
    )
    st.divider()
    st.metric(
        label=f"EUR at {q_aband:.1f} Sm³/day econ. limit",
        value=f"{eur_val / 1_000_000:.3f} MSm³",
    )

# ── Main area ─────────────────────────────────────────────────────────────────
st.title("DCA Forecast")
st.caption("Select a fitting window, click Auto-Fit, then tune parameters with the sliders.")

# Fit error banner
if st.session_state.get("dca_fit_error"):
    st.error(st.session_state["dca_fit_error"])

# Goodness-of-fit metrics (shown only after first fit)
if st.session_state["dca_fitted"]:
    m1, m2, m3 = st.columns(3)
    m1.metric("R²", f"{st.session_state['dca_r2']:.4f}",
              help="Closer to 1.0 is better. Below 0.85 suggests poor fit window.")
    m2.metric("RMSE (Sm³/day)", f"{st.session_state['dca_rmse']:,.1f}")
    m3.metric("Model", st.session_state["dca_model"].capitalize())

    # Harmonic singularity warning
    if abs(st.session_state["dca_b"] - 1.0) < 0.01:
        st.warning("b ≈ 1.0 — Using harmonic Arps equations (prevents infinite EUR).")

# Live LaTeX equation
st.latex(
    get_latex_equation(
        model=model,
        qi=st.session_state["dca_qi"],
        Di=st.session_state["dca_Di"],
        b=st.session_state["dca_b"],
    )
)

st.divider()

# Build chart: historical + fitted/forecast
df_fit_window = filter_by_date(df, start_date, end_date) if start_date and end_date else None
df_forecast = None
if st.session_state["dca_fitted"] or True:
    # Always show forecast from current slider values
    fit_result_for_chart = {
        "qi": st.session_state["dca_qi"],
        "Di": st.session_state["dca_Di"],
        "b": st.session_state["dca_b"],
        "model": model,
        "t0": st.session_state.get("dca_t0") or df["DATEPRD"].iloc[0],
    }
    df_forecast = forecast_arps(fit_result_for_chart, forecast_months=forecast_months, q_aband=q_aband)

fig = build_dca_chart(
    df_all=df,
    df_fit_window=df_fit_window,
    df_forecast=df_forecast,
)
st.plotly_chart(fig, theme=None, use_container_width=True)
