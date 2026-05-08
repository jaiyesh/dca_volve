import streamlit as st
from utils.data import load_data, get_sidebar_kpis
from utils.charts import build_timeseries_chart, build_dual_axis_chart

st.set_page_config(page_title="Production Explorer — Volve DCA", layout="wide")

df = load_data()
kpis = get_sidebar_kpis(df)

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Volve DCA Dashboard")
    st.caption("Well: **15/9-F-12**")
    st.caption(f"Period: {kpis['date_start']} – {kpis['date_end']}")
    st.metric("Total Oil", f"{kpis['total_oil_mmsm3']:.3f} MSm³")
    st.metric("Peak Rate", f"{kpis['peak_rate']:,} Sm³/day")
    st.metric("On-stream Days", f"{kpis['on_stream_days']:,}")

# ── Main content ─────────────────────────────────────────────────────────────
st.title("Production Explorer")
st.caption("Time-series charts for well 15/9-F-12. Hover to inspect values; drag to zoom.")

# Chart 1: Oil rate
fig_oil = build_timeseries_chart(
    df, "BORE_OIL_VOL",
    title="Oil Production Rate",
    y_label="Oil Rate (Sm³/day)",
    color="#FF6B35",
)
st.plotly_chart(fig_oil, theme=None, width="stretch")

# Chart 2: Gas rate
fig_gas = build_timeseries_chart(
    df, "BORE_GAS_VOL",
    title="Gas Production Rate",
    y_label="Gas Rate (Sm³/day)",
    color="#00D4FF",
)
st.plotly_chart(fig_gas, theme=None, width="stretch")

# Chart 3: Water cut
fig_wc = build_timeseries_chart(
    df, "WATER_CUT",
    title="Water Cut",
    y_label="Water Cut (fraction)",
    color="#FF4B4B",
)
st.plotly_chart(fig_wc, theme=None, width="stretch")

# Chart 4: WHP + choke size (dual axis)
fig_whp = build_dual_axis_chart(
    df,
    y1_col="AVG_WHP_P",
    y1_label="WHP (bar)",
    y1_color="#FFD700",
    y2_col="AVG_CHOKE_SIZE_P",
    y2_label="Choke Size (%)",
    y2_color="#AAAAAA",
    title="Wellhead Pressure & Choke Size",
)
st.plotly_chart(fig_whp, theme=None, width="stretch")
